"""MCP functions against actual commerce routes and account API keys."""
import json
from uuid import uuid4


def test_all_nine_mcp_functions_with_account_keys(client):
    def account():
        signup = client.post('/v1/auth/users', headers={'Authorization':''}, json={
            'email':f'mcp_{uuid4().hex}@test.com', 'password':'password123', 'display_name':'MCP test',
        })
        assert signup.status_code == 201, signup.text
        jwt = {'Authorization':'Bearer '+signup.json()['access_token']}
        user = client.get('/v1/users/me',headers=jwt).json()
        key = client.post('/v1/keys/account',headers=jwt)
        assert key.status_code == 201, key.text
        return user, jwt, key.json()['key']

    owner, jwt, key = account()
    _, _, redeemer_key = account()
    deposit = client.post('/v1/ledger/deposit',headers=jwt,json={
        'account_owner_type':'user','account_owner_id':owner['id'],
        'amount':{'amount':'10','currency':'ACP'},'reference':'mcp-local-fixture',
    })
    assert deposit.status_code == 201, deposit.text

    def call(name,args,credential=key):
        response = client.post('/v1/mcp', headers={'Authorization':'Bearer '+credential}, json={
            'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args},
        })
        assert response.status_code == 200, response.text
        body=response.json()
        assert 'error' not in body, body
        assert not body['result'].get('isError'), body
        return json.loads(body['result']['content'][0]['text'])

    link=call('ancap.create_payment_link',{'title':'MCP invoice','amount':'1'})
    assert call('ancap.check_payment_status',{'code':link['code']})['status']=='pending'
    invoice=call('ancap.create_invoice',{'line_items':[{'description':'Research','unit_amount':'1'}]})
    assert invoice['invoice_number']
    claim=call('ancap.create_claim_code',{'amount':'1'})
    assert call('ancap.redeem_claim_code',{'code':claim['code']},redeemer_key)['status']=='redeemed'
    preview=call('ancap.quote_smart_pay',{'raw_text':'https://ancap.cloud/pay/'+link['code']})
    assert preview['requires_manual_confirm'] is True
    assert call('ancap.token_snapshot',{'token':'ACP'})['id']
    assert call('ancap.create_risk_report',{'token':'ACP'})['id']
    assert call('ancap.run_workflow',{'workflow_slug':'token-risk-report','unlock_full_result':False})['id']


def test_quality_admin_fails_closed_without_operator_allowlist(client):
    # The legacy quality router currently carries its own /v1 prefix.
    response = client.get('/v1/v1/quality-fixtures/')
    assert response.status_code == 503, response.text
