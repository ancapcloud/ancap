from decimal import Decimal
from uuid import uuid4


def _register_user(client, label: str):
    email = f"{label}_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": label},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user = client.get("/v1/users/me", headers=headers).json()
    return user, headers


def _deposit(client, user_id: str, amount: str, headers):
    res = client.post(
        "/v1/ledger/deposit",
        headers=headers,
        json={
            "account_owner_type": "user",
            "account_owner_id": user_id,
            "amount": {"amount": amount, "currency": "ACP"},
            "reference": "merchant-pay-test",
        },
    )
    assert res.status_code == 201, res.text


def test_payment_link_create_and_checkout(client):
    merchant_user, merchant_headers = _register_user(client, "merchant_owner")
    payer_user, payer_headers = _register_user(client, "merchant_payer")
    _deposit(client, payer_user["id"], "50", payer_headers)

    create = client.post(
        "/v1/pay/payment-links",
        headers=merchant_headers,
        json={"title": "Test link", "amount": "12.5", "currency": "ACP"},
    )
    assert create.status_code == 201, create.text
    link = create.json()
    assert link["status"] == "pending"
    code = link["code"]

    public = client.get(f"/v1/pay/{code}")
    assert public.status_code == 200, public.text
    assert Decimal(public.json()["amount"]) == Decimal("12.5")

    checkout = client.post(
        f"/v1/pay/{code}/checkout",
        headers=payer_headers,
        json={"payment_method": "credits"},
    )
    assert checkout.status_code == 200, checkout.text
    body = checkout.json()
    assert body["status"] == "captured"
    assert body["payment_link"]["status"] == "paid"

    dashboard = client.get("/v1/merchant/dashboard", headers=merchant_headers)
    assert dashboard.status_code == 200, dashboard.text
    dash = dashboard.json()
    assert dash["paid_links"] >= 1
    assert Decimal(dash["total_volume_acp"]) >= Decimal("12.5")


def test_merchant_cannot_pay_own_link(client):
    user, headers = _register_user(client, "self_pay")
    _deposit(client, user["id"], "20", headers)
    create = client.post(
        "/v1/pay/payment-links",
        headers=headers,
        json={"title": "Self", "amount": "5", "currency": "ACP"},
    )
    assert create.status_code == 201, create.text
    code = create.json()["code"]
    checkout = client.post(f"/v1/pay/{code}/checkout", headers=headers, json={"payment_method": "credits"})
    assert checkout.status_code == 400, checkout.text


def test_invoice_rejects_invalid_quantities_and_mixed_currencies(client):
    _, headers = _register_user(client, "invoice_validation")
    for quantity in ["0", "-1", "NaN", "Infinity"]:
        response = client.post('/v1/pay/invoices', headers=headers, json={
            'line_items':[{'description':'Invalid', 'unit_amount':'1','quantity':quantity}],
        })
        assert response.status_code == 422, response.text
    response = client.post('/v1/pay/invoices', headers=headers, json={
        'line_items':[{'description':'First','unit_amount':'1','currency':'ACP'},
                      {'description':'Second','unit_amount':'1','currency':'USD'}],
    })
    assert response.status_code == 400
    for amount in ['NaN','sNaN','Infinity','1e100','1e-30']:
        response = client.post('/v1/pay/payment-links',headers=headers,json={'title':'Invalid','amount':amount})
        assert response.status_code == 400, response.text
