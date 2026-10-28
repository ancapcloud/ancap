"""Synthetic completed reports test binding/replay, not paid customer acceptance."""
import asyncio
import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from test_research_operations_api import setup, add, age, register
from app.services import workflow_ops, research_fetch
from app.db.models import WorkflowOperationRun
from app.db.session import SessionLocal


@pytest.fixture(autouse=True)
def remove_synthetic_packet_operations(db_cursor):
    # These fixtures do not belong to the worker queue exercised by other tests.
    db_cursor.execute("DELETE FROM workflow_operation_runs WHERE request_key LIKE 'packet-%'")
    db_cursor.connection.commit()
    yield
    db_cursor.execute("DELETE FROM workflow_operation_runs WHERE request_key LIKE 'packet-%'")
    db_cursor.connection.commit()


def fixture(client, db_cursor, monkeypatch, connection=False):
    user, headers, pid, base = setup(client)
    source_id = add(client, headers, base)
    html = [b'<p>Product source version one</p>']
    async def fetch(_): return research_fetch.extract_page(html[0])
    monkeypatch.setattr(research_fetch, 'fetch_page', fetch)
    checked = client.post(f'{base}/sources/{source_id}/check', headers=headers)
    assert checked.status_code == 200
    assert client.post(base+'/claims',headers=headers,json={'source_id':source_id,
        'source_hash':checked.json()['snapshot']['hash'],'statement':'The source describes product version one',
        'excerpt':'Product source version one','verdict':'supported_by_source'}).status_code==201
    result = {'summary':'Existing report fixture'}
    quoted = client.post('/v1/workflow-store/runs', headers=headers, json={
        'workflow_slug':'token-risk-report','payment_currency':'ACP','unlock_full_result':False,'inputs':{'project_name':'Research packet fixture'}})
    assert quoted.status_code == 201, quoted.text
    rid = quoted.json()['id']
    db_cursor.execute("UPDATE workflow_runs SET status='completed',result_json=%s::jsonb WHERE id=%s", (json.dumps(result),rid))
    definition = {'name':'Research report','project_id':pid,'steps':[{'slug':'token-risk-report'}],'require_review':True,'connection_ids':[]}
    automation = client.post('/v1/workflow-ops/automations', headers=headers, json=definition)
    assert automation.status_code == 201,automation.text
    if connection:
        cid = str(uuid4())
        db_cursor.execute("INSERT INTO workflow_connections(id,owner_user_id,name,kind,config_json,secret_box,allow_delivery,created_at) VALUES(%s,%s,'Mock channel','webhook','{}','fixture',TRUE,NOW())",(cid,user['id']))
        definition['connection_ids']=[cid]
    op_id = str(uuid4())
    progress={'items':[{'run_id':rid,'output':result,'quality':{'passed':True}}], 'deliveries':[]}
    db_cursor.execute("INSERT INTO workflow_operation_runs(id,owner_user_id,automation_id,request_key,request_hash,kind,state,snapshot_json,progress_json,cost_acp,max_cost_acp,created_at,expires_at) VALUES(%s,%s,%s,%s,%s,'manual','awaiting_review',%s::jsonb,%s::jsonb,0,1,NOW(),NOW()+interval '7 days')",
        (op_id,user['id'],automation.json()['id'],'packet-'+op_id,'a'*64,json.dumps({'definition':definition}),json.dumps(progress)))
    db_cursor.connection.commit()
    monkeypatch.setattr(workflow_ops,'async_session_maker',SessionLocal)
    return user,headers,pid,base,source_id,rid,op_id,html


def get(client,headers,op):
    r=client.get('/v1/workflow-ops/runs/'+op,headers=headers)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()


def attach(client,headers,base,source_id,op):
    r=client.post(base+'/packets',headers=headers,json={'operation_id':op,'source_ids':[source_id],
        'expected_review_hash':get(client,headers,op)['review_hash']})
    assert r.status_code==201,r.text
    return r.json()


def approve(client,headers,op,**extra):
    return client.post('/v1/workflow-ops/runs/'+op+'/review',headers=headers,json={
        'decision':'approve','expected_review_hash':get(client,headers,op)['review_hash'],**extra})


async def claim(op_id):
    async with SessionLocal() as session:
        op=await session.get(WorkflowOperationRun,op_id)
        delivery=await workflow_ops._process_delivery(session,op)
        await session.commit()
        return delivery


def test_exact_packet_review_edit_and_outbox_replay_without_new_charge(client,db_cursor,monkeypatch):
    _,headers,_,base,sid,_,op,_=fixture(client,db_cursor,monkeypatch,connection=True)
    db_cursor.execute('SELECT count(*) FROM payment_intents');before=db_cursor.fetchone()[0]
    packet=attach(client,headers,base,sid,op)
    saved=packet['progress']['research_packets'][0]
    assert saved['packet']['format']=='ancap-research-client-packet/v1'
    assert len(saved['packet']['workflow_versions'])==1 and saved['version']==1
    assert client.post('/v1/workflow-ops/runs/'+op+'/review',headers=headers,json={'decision':'approve'}).status_code==409
    assert client.post('/v1/workflow-ops/runs/'+op+'/review',headers=headers,json={'decision':'approve','expected_review_hash':'b'*64}).status_code==409
    accepted=approve(client,headers,op,edited_output={'summary':'Human-edited result'})
    assert accepted.status_code==200,accepted.text
    output=accepted.json()['progress']['reviewed_output']
    assert output['result']=={'summary':'Human-edited result'}
    assert output['research']==saved['packet']['research']
    assert 'permission_basis' not in output['research']['sources'][0]
    assert 'reviewer_user_id' not in output['research']['claims'][0]
    sent=[]
    async def delivery(channel,run,payload):
        sent.append(payload)
        return {'connection_id':str(channel.id),'state':'delivered'}
    monkeypatch.setattr(workflow_ops,'deliver',delivery)
    outbox=asyncio.run(claim(op));assert outbox
    asyncio.run(workflow_ops._send_prepared_delivery(outbox))
    asyncio.run(workflow_ops._send_prepared_delivery(outbox))
    assert asyncio.run(claim(op)) is None
    assert sent==[output]
    assert approve(client,headers,op).status_code==409
    db_cursor.execute('SELECT count(*) FROM payment_intents');assert db_cursor.fetchone()[0]==before


def test_source_change_requires_new_packet_and_retains_old_version(client,db_cursor,monkeypatch):
    _,headers,_,base,sid,_,op,html=fixture(client,db_cursor,monkeypatch)
    original=attach(client,headers,base,sid,op)['progress']['research_packets'][0]
    html[0]=b'<p>Product source version two</p>';age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).status_code==200
    assert approve(client,headers,op).status_code==409
    updated=attach(client,headers,base,sid,op)
    assert updated['progress']['research_packets'][0]==original
    assert len(updated['progress']['research_packets'])==2
    assert updated['progress']['research_packets'][1]['hash']!=original['hash']
    assert approve(client,headers,op).status_code==200


def test_changed_evidence_after_outbox_claim_is_blocked_before_send(client,db_cursor,monkeypatch):
    _,headers,_,base,sid,_,op,html=fixture(client,db_cursor,monkeypatch,connection=True)
    attach(client,headers,base,sid,op);assert approve(client,headers,op).status_code==200
    outbox=asyncio.run(claim(op));assert outbox
    html[0]=b'<p>New evidence after approval</p>';age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).status_code==200
    async def forbidden(*args):raise AssertionError('Stale packet must never reach the channel')
    monkeypatch.setattr(workflow_ops,'deliver',forbidden)
    asyncio.run(workflow_ops._send_prepared_delivery(outbox))
    state=get(client,headers,op)
    assert state['state']=='failed' and state['progress']['deliveries'][0]['state']=='blocked'


def test_base_result_change_revoked_access_and_expiry_fail_closed(client,db_cursor,monkeypatch):
    owner,headers,pid,base,sid,rid,op,_=fixture(client,db_cursor,monkeypatch)
    attached=attach(client,headers,base,sid,op)
    viewer,view_headers=register(client)
    assert client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=headers,json={'email':viewer['email'],'role':'viewer'}).status_code==200
    body={'operation_id':op,'source_ids':[sid],'expected_review_hash':attached['review_hash']}
    assert client.post(base+'/packets',headers=view_headers,json=body).status_code==404
    assert client.get('/v1/workflow-ops/runs/'+op,headers=view_headers).status_code==200
    assert client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=headers,json={'email':viewer['email'],'role':'remove'}).status_code==200
    assert client.get('/v1/workflow-ops/runs/'+op,headers=view_headers).status_code==404
    assert op not in [r['id'] for r in client.get('/v1/workflow-ops',headers=view_headers).json()['runs']]
    db_cursor.execute('UPDATE workflow_runs SET result_json=%s::jsonb WHERE id=%s',(json.dumps({'summary':'Changed unseen result'}),rid));db_cursor.connection.commit()
    assert approve(client,headers,op).status_code==409
    db_cursor.execute("UPDATE workflow_operation_runs SET expires_at=NOW()-interval '1 second' WHERE id=%s",(op,));db_cursor.connection.commit()
    assert client.get('/v1/workflow-ops/runs/'+op,headers=headers).status_code==404
    assert op not in [r['id'] for r in client.get('/v1/workflow-ops',headers=headers).json()['runs']]


def test_revoked_original_run_owner_cannot_read_or_deliver_packet(client,db_cursor,monkeypatch):
    owner,headers,pid,base,sid,_,op,_=fixture(client,db_cursor,monkeypatch,connection=True)
    attach(client,headers,base,sid,op);assert approve(client,headers,op).status_code==200
    project_owner,project_headers=register(client)
    db_cursor.execute('UPDATE workflow_projects SET owner_user_id=%s,members_json=%s::jsonb WHERE id=%s',
        (project_owner['id'],json.dumps({owner['id']:'editor'}),pid));db_cursor.connection.commit()
    assert client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=project_headers,json={'email':owner['email'],'role':'remove'}).status_code==200
    assert client.get('/v1/workflow-ops/runs/'+op,headers=headers).status_code==404
    assert op not in [r['id'] for r in client.get('/v1/workflow-ops',headers=headers).json()['runs']]
    with pytest.raises(HTTPException):asyncio.run(claim(op))


def test_changed_approved_output_cannot_be_dispatched(client,db_cursor,monkeypatch):
    _,headers,_,base,sid,_,op,_=fixture(client,db_cursor,monkeypatch,connection=True)
    attach(client,headers,base,sid,op);assert approve(client,headers,op).status_code==200
    db_cursor.execute("UPDATE workflow_operation_runs SET progress_json=jsonb_set(progress_json,'{reviewed_output,result}',%s::jsonb) WHERE id=%s",(json.dumps({'summary':'Unseen change'}),op));db_cursor.connection.commit()
    with pytest.raises(HTTPException):asyncio.run(claim(op))


def test_text_shortening_channels_cannot_receive_research_packets(client,db_cursor,monkeypatch):
    _,headers,_,base,sid,_,op,_=fixture(client,db_cursor,monkeypatch,connection=True)
    db_cursor.execute("UPDATE workflow_connections SET kind='telegram' WHERE id=(SELECT (snapshot_json->'definition'->'connection_ids'->>0)::uuid FROM workflow_operation_runs WHERE id=%s)",(op,));db_cursor.connection.commit()
    r=client.post(base+'/packets',headers=headers,json={'operation_id':op,'source_ids':[sid],
        'expected_review_hash':get(client,headers,op)['review_hash']})
    assert r.status_code==409


@pytest.mark.parametrize("denial", ["revoked", "expired"])
def test_retry_and_cancel_do_not_disclose_inaccessible_packets(client, db_cursor, monkeypatch, denial):
    _, headers, pid, base, sid, _, op, _ = fixture(client, db_cursor, monkeypatch, connection=True)
    attach(client, headers, base, sid, op)
    approved = approve(client, headers, op)
    assert approved.status_code == 200
    db_cursor.execute("SELECT snapshot_json->'definition'->'connection_ids'->>0 FROM workflow_operation_runs WHERE id=%s", (op,))
    cid = db_cursor.fetchone()[0]
    db_cursor.execute("UPDATE workflow_operation_runs SET state='completed',progress_json=jsonb_set(progress_json,'{deliveries}',%s::jsonb) WHERE id=%s",
        (json.dumps([{'connection_id': cid, 'state': 'unknown_or_failed'}]), op))
    if denial == "revoked":
        new_owner, _ = register(client)
        db_cursor.execute("UPDATE workflow_projects SET owner_user_id=%s,members_json='{}'::jsonb WHERE id=%s", (new_owner['id'], pid))
    else:
        db_cursor.execute("UPDATE workflow_operation_runs SET expires_at=NOW()-interval '1 second' WHERE id=%s", (op,))
    db_cursor.connection.commit()
    retry = client.post(f'/v1/workflow-ops/runs/{op}/retry-delivery', headers=headers,
        json={'connection_id': cid, 'confirm_retry': True})
    assert retry.status_code == 404
    assert 'research_packets' not in retry.text
    db_cursor.execute("SELECT state,progress_json->'deliveries' FROM workflow_operation_runs WHERE id=%s", (op,))
    state, deliveries = db_cursor.fetchone()
    assert state == 'completed' and deliveries[0]['state'] == 'unknown_or_failed'
    db_cursor.execute("UPDATE workflow_operation_runs SET state='queued' WHERE id=%s", (op,))
    db_cursor.connection.commit()
    cancelled = client.post(f'/v1/workflow-ops/runs/{op}/cancel', headers=headers)
    assert cancelled.status_code == 404
    assert 'research_packets' not in cancelled.text
    db_cursor.execute("SELECT state FROM workflow_operation_runs WHERE id=%s", (op,))
    assert db_cursor.fetchone()[0] == 'queued'
