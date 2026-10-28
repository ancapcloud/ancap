import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.services import research_fetch


def register(client):
    r=client.post('/v1/auth/users', headers={'Authorization':''}, json={
        'email':f'research-{uuid4().hex}@test.com','password':'research-test-123','display_name':'Research fixture'})
    assert r.status_code == 201, r.text
    headers={'Authorization':'Bearer '+r.json()['access_token']}
    return client.get('/v1/users/me',headers=headers).json(),headers


def setup(client):
    user,headers=register(client)
    p=client.post('/v1/workflow-ops/projects',headers=headers,json={'name':'Research pilot','retention_days':7})
    assert p.status_code==201,p.text
    pid=p.json()['id'];base=f'/v1/workflow-ops/projects/{pid}/research'
    return user,headers,pid,base


def add(client,headers,base,url='https://example.org/'):
    r=client.post(base+'/sources',headers=headers,json={'title':'Approved source','url':url,'permission_basis':'Permission supplied by source owner'})
    assert r.status_code==201,r.text
    return r.json()['id']


def age(db_cursor,sid):
    db_cursor.execute("UPDATE research_sources SET checked_at=NOW()-interval '2 minutes' WHERE id=%s",(sid,))
    db_cursor.connection.commit()


def test_source_claim_version_change_failure_and_no_payment(client,db_cursor,monkeypatch):
    _,headers,pid,base=setup(client);sid=add(client,headers,base)
    body=b'<h1>Product</h1><p>Price 10 EUR</p>'
    async def fetch(_): return research_fetch.extract_page(body)
    monkeypatch.setattr(research_fetch,'fetch_page',fetch)
    db_cursor.execute('SELECT count(*) FROM payment_intents');payments=db_cursor.fetchone()[0]
    r=client.post(f'{base}/sources/{sid}/check',headers=headers)
    assert r.status_code==200,r.text
    assert r.json()['change']=='baseline' and r.headers['cache-control']=='private, no-store'
    digest=r.json()['snapshot']['hash']
    claim={'source_id':sid,'source_hash':digest,'statement':'The source lists a 10 EUR price',
        'excerpt':'Price 10 EUR','verdict':'supported_by_source'}
    assert client.post(base+'/claims',headers=headers,json={**claim,'excerpt':'invented quotation'}).status_code==422
    assert client.post(base+'/claims',headers=headers,json=claim).status_code==201
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).status_code==429
    age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).json()['change']=='unchanged'
    body=b'<h1 class="new">Product</h1><p>Price 10 EUR</p><script>ignored</script>'
    age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).json()['change']=='technical'
    assert client.get(base,headers=headers).json()['claims'][0]['status']=='supported_by_source'
    body=b'<h1>Product</h1><p>Price 20 EUR</p>'
    age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).json()['change']=='content_change_requires_review'
    brief=client.get(base,headers=headers)
    assert brief.json()['project_name']=='Research pilot'
    assert brief.json()['claims'][0]['status']=='requires_update'
    assert brief.json()['delivery_enabled'] is False and brief.json()['state']=='draft_requires_review'
    assert brief.json()['independent_fact_check'] is False
    assert client.post(base+'/claims',headers=headers,json=claim).status_code==409
    async def fail(_): raise TimeoutError()
    monkeypatch.setattr(research_fetch,'fetch_page',fail)
    age(db_cursor,sid)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).json()['change']=='unavailable'
    assert client.get(base,headers=headers).json()['claims'][0]['status']=='source_unavailable'
    versions=client.get(f'{base}/sources/{sid}/snapshots',headers=headers)
    assert len(versions.json())==3
    assert {s['text'] for s in versions.json()}=={'Product Price 10 EUR','Product Price 20 EUR'}
    db_cursor.execute('SELECT count(*) FROM payment_intents');assert db_cursor.fetchone()[0]==payments


def test_cross_project_isolation_guest_and_read_only_member(client,monkeypatch):
    _,headers,pid,base=setup(client);sid=add(client,headers,base)
    viewer,view_headers=register(client);_,foreign=register(client)
    assert client.get(base,headers={'Authorization':''}).status_code==401
    assert client.get(base,headers=foreign).status_code==404
    assert client.post(f'{base}/sources/{sid}/check',headers=foreign).status_code==404
    assert client.get(f'{base}/sources/{sid}/snapshots',headers=foreign).status_code==404
    result=client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=headers,json={'email':viewer['email'],'role':'viewer'})
    assert result.status_code==200,result.text
    assert client.get(base,headers=view_headers).status_code==200
    assert client.post(f'{base}/sources/{sid}/check',headers=view_headers).status_code==404
    assert client.post(base+'/sources',headers=view_headers,json={'title':'No','url':'https://example.net/','permission_basis':'Approved by owner'}).status_code==404
    response = client.delete(f'{base}/sources/{sid}',headers=view_headers)
    assert response.status_code == 404
    changed=client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=headers,json={'email':viewer['email'],'role':'editor'})
    assert changed.status_code==200,changed.text
    editable=add(client,view_headers,base,'https://example.net/')
    response = client.delete(f'{base}/sources/{editable}',headers=view_headers)
    assert response.status_code == 200
    response = client.post(f'/v1/workflow-ops/projects/{pid}/members',headers=headers,json={'email':viewer['email'],'role':'remove'})
    assert response.status_code == 200
    assert client.get(base,headers=view_headers).status_code==404
    _,other_headers,_,other_base=setup(client)
    assert client.get(f'{other_base}/sources/{sid}/snapshots',headers=other_headers).status_code==404
    assert client.post(f'{other_base}/sources/{sid}/check',headers=other_headers).status_code==404


def test_source_limits_duplicate_retention_and_project_delete(client,db_cursor,monkeypatch):
    _,headers,pid,base=setup(client);sid=add(client,headers,base)
    body={'title':'Duplicate','url':'https://example.org/','permission_basis':'Approved public source collection'}
    assert client.post(base+'/sources',headers=headers,json=body).status_code==409
    for i in range(9): add(client,headers,base,f'https://example.org/source-{i}')
    assert client.post(base+'/sources',headers=headers,json={**body,'url':'https://example.org/overflow'}).status_code==409
    async def fetch(_): return research_fetch.extract_page(b'<p>Original evidence</p>')
    monkeypatch.setattr(research_fetch,'fetch_page',fetch)
    checked=client.post(f'{base}/sources/{sid}/check',headers=headers).json()
    assert client.post(base+'/claims',headers=headers,json={'source_id':sid,'source_hash':checked['snapshot']['hash'],
        'statement':'Original claim','excerpt':'Original evidence','verdict':'unconfirmed'}).status_code==201
    db_cursor.execute("UPDATE research_sources SET expires_at=NOW()-interval '1 second' WHERE id=%s",(sid,));db_cursor.connection.commit()
    assert len(client.get(base,headers=headers).json()['sources'])==9
    assert client.get(f'{base}/sources/{sid}/snapshots',headers=headers).status_code==404
    assert client.get(base,headers=headers).json()['claims']==[]
    async def purge():
        from app.db.session import SessionLocal
        from app.services.research_ops import purge_expired
        async with SessionLocal() as session:
            await purge_expired(session)
            await session.commit()
    asyncio.run(purge())
    db_cursor.execute('SELECT count(*) FROM research_snapshots WHERE source_id=%s',(sid,))
    assert db_cursor.fetchone()[0]==0
    db_cursor.execute('SELECT count(*) FROM research_claims WHERE source_id=%s',(sid,))
    assert db_cursor.fetchone()[0]==0
    response = client.delete(f'/v1/workflow-ops/projects/{pid}',headers=headers)
    assert response.status_code == 200
    for table in ('research_sources','research_snapshots','research_claims'):
        column='project_id' if table=='research_sources' else 'source_id'
        db_cursor.execute(f'SELECT count(*) FROM {table} WHERE {column}=%s',(pid if column=='project_id' else sid,))
        assert db_cursor.fetchone()[0]==0


def test_version_limit_prevents_network_work(client,db_cursor,monkeypatch):
    _,headers,_,base=setup(client);sid=add(client,headers,base)
    for _ in range(20):
        db_cursor.execute("INSERT INTO research_snapshots(id,source_id,raw_hash,text_hash,text_content,change_kind,created_at) VALUES(%s,%s,%s,%s,'fixture','baseline',NOW())",(str(uuid4()),sid,'a'*64,'b'*64))
    db_cursor.connection.commit()
    async def forbidden(_): raise AssertionError('Quota must stop before any network access')
    monkeypatch.setattr(research_fetch,'fetch_page',forbidden)
    assert client.post(f'{base}/sources/{sid}/check',headers=headers).status_code==409


def test_concurrent_checks_fetch_once(client,monkeypatch):
    _,headers,_,base=setup(client);sid=add(client,headers,base)
    calls=[]
    async def fetch(_):
        calls.append('fetch')
        await asyncio.sleep(0.15)
        return research_fetch.extract_page(b'<p>One observed version</p>')
    monkeypatch.setattr(research_fetch,'fetch_page',fetch)
    def check(_):return client.post(f'{base}/sources/{sid}/check',headers=headers).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(check,range(2)))
    assert sorted(statuses)==[200,429]
    assert calls==['fetch']
