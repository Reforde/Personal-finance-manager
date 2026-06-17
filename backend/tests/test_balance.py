def test_get_balance_empty(auth_client):
    res = auth_client.get('/api/balance/2025-06')
    assert res.status_code == 200
    data = res.get_json()
    assert data['month'] == '2025-06'
    assert data['amount'] == 0


def test_set_balance(auth_client):
    res = auth_client.put('/api/balance/2025-06', json={'amount': 50000})
    assert res.status_code == 200
    assert res.get_json()['amount'] == 50000


def test_set_balance_updates_existing(auth_client):
    auth_client.put('/api/balance/2025-06', json={'amount': 50000})
    res = auth_client.put('/api/balance/2025-06', json={'amount': 99999})
    assert res.status_code == 200
    assert res.get_json()['amount'] == 99999


def test_get_balance_after_set(auth_client):
    auth_client.put('/api/balance/2025-06', json={'amount': 123456})
    res = auth_client.get('/api/balance/2025-06')
    assert res.status_code == 200
    assert res.get_json()['amount'] == 123456


def test_balance_different_months_are_independent(auth_client):
    auth_client.put('/api/balance/2025-05', json={'amount': 10000})
    auth_client.put('/api/balance/2025-06', json={'amount': 20000})

    assert auth_client.get('/api/balance/2025-05').get_json()['amount'] == 10000
    assert auth_client.get('/api/balance/2025-06').get_json()['amount'] == 20000


def test_set_balance_zero(auth_client):
    res = auth_client.put('/api/balance/2025-06', json={'amount': 0})
    assert res.status_code == 200
    assert res.get_json()['amount'] == 0


def test_set_balance_negative(auth_client):
    res = auth_client.put('/api/balance/2025-06', json={'amount': -5000})
    assert res.status_code == 200
    assert res.get_json()['amount'] == -5000


def test_balance_invalid_month_format(auth_client):
    res = auth_client.get('/api/balance/invalid')
    assert res.status_code == 422

    res = auth_client.get('/api/balance/2025-6')
    assert res.status_code == 422


def test_balance_invalid_amount(auth_client):
    res = auth_client.put('/api/balance/2025-06', json={'amount': 'not-a-number'})
    assert res.status_code == 422


def test_balance_missing_amount(auth_client):
    res = auth_client.put('/api/balance/2025-06', json={})
    assert res.status_code == 422


def test_balance_unauthenticated(client):
    res = client.get('/api/balance/2025-06')
    assert res.status_code == 401

    res = client.put('/api/balance/2025-06', json={'amount': 100})
    assert res.status_code == 401
