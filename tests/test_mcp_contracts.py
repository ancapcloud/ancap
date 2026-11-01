"""Regression tests for MCP dispatch contracts and legacy stream delivery (no DB)."""
import asyncio
import importlib.util
import io
import json
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from starlette.requests import Request as StarletteRequest

from app.api.routers.mcp import _SSE_SESSIONS, mcp_legacy_sse, mcp_legacy_message
from app.services.mcp_remote import TOOL_DEFS, dispatch_tool, extract_api_key


@pytest.mark.asyncio
@pytest.mark.parametrize('name,args,expected', [
    ('ancap.token_snapshot', {'token':'ACP'}, {'workflow_slug':'token-risk-report','unlock_full_result':False}),
    ('ancap.create_risk_report', {'token':'ACP'}, {'workflow_slug':'token-risk-report-pro','unlock_full_result':True}),
    ('ancap.create_payment_link', {'title':'Test','amount':'1'}, {'title':'Test','amount':'1'}),
    ('ancap.create_invoice', {'line_items':[{'description':'Research','unit_amount':'1'}]}, {'create_payment_link':True}),
    ('ancap.check_payment_status', {'code':'abc123'}, {}),
    ('ancap.create_claim_code', {'amount':'1'}, {'amount':'1','max_redemptions':1}),
    ('ancap.redeem_claim_code', {'code':'abcdef'}, {'code':'abcdef'}),
    ('ancap.quote_smart_pay', {'raw_text':'acp:test'}, {'raw_text':'acp:test'}),
    ('ancap.quote_smart_pay', {'raw':'acp:test'}, {'raw_text':'acp:test'}),
    ('ancap.run_workflow', {'workflow_slug':'token-risk-report','unlock_full_result':False}, {'workflow_slug':'token-risk-report','unlock_full_result':False}),
])
async def test_every_function_dispatches_valid_payload(name, args, expected):
    app = FastAPI()
    captured = {}

    async def target(request: Request):
        captured.update(await request.json() if request.method == 'POST' else {})
        assert request.headers['x-api-key'] == 'ancap_test'
        assert request.headers['authorization'] == 'Bearer ancap_test'
        assert 'api_key' not in captured
        return {'ok': True}

    path = TOOL_DEFS[name]['path'] or '/pay/abc123'
    app.add_api_route('/v1'+path, target, methods=[TOOL_DEFS[name]['method']])
    result = await dispatch_tool(app=app, name=name, arguments={**args,'api_key':'ancap_test'}, api_key='ancap_test')
    assert result == {'ok':True}
    assert all(captured[k] == v for k,v in expected.items())


@pytest.mark.asyncio
async def test_legacy_response_delivered_on_stream_and_session_cleaned_up():
    app = FastAPI()
    async def receive():
        await asyncio.sleep(3600)
    request = StarletteRequest({'type':'http','method':'GET','path':'/v1/mcp/sse','headers':[], 'app':app}, receive)
    response = await mcp_legacy_sse(request)
    iterator = response.body_iterator
    endpoint = await anext(iterator)
    session = endpoint.split('sessionId=')[1].strip()
    body = json.dumps({'jsonrpc':'2.0','id':9,'method':'ping'}).encode()
    async def post_receive():
        return {'type':'http.request','body':body,'more_body':False}
    post = StarletteRequest({'type':'http','method':'POST','path':'/v1/mcp/message','headers':[], 'app':app}, post_receive)
    accepted = await mcp_legacy_message(post, sessionId=session, authorization=None, x_api_key=None)
    assert accepted.status_code == 202
    event = await anext(iterator)
    assert 'event: message' in event
    assert json.loads(event.split('data: ')[1]) == {'jsonrpc':'2.0','id':9,'result':{}}
    await iterator.aclose()
    assert session not in _SSE_SESSIONS


def test_transport_credentials_override_tool_arguments():
    assert extract_api_key('Bearer ancap_header', None, {'api_key':'ancap_argument'}) == 'ancap_header'


def test_stdio_forwards_catalogue_and_recovers_from_bad_json(monkeypatch):
    spec = importlib.util.spec_from_file_location('ancap_stdio', Path('mcp-server/ancap_mcp_server.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, '_handle_message', lambda message: {'jsonrpc':'2.0','id':message['id'],'result':{'tools':[]}})
    monkeypatch.setattr(module.sys, 'stdin', io.StringIO('invalid\n{"id": 2}\n'))
    output = io.StringIO()
    monkeypatch.setattr(module.sys, 'stdout', output)
    module.main()
    first, second = map(json.loads, output.getvalue().splitlines())
    assert first['error']['code'] == -32700
    assert second['id'] == 2
