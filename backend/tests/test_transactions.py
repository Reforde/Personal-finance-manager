from datetime import datetime
from app.models import Transaction


def _create_manual(client, **kwargs):
    payload = {
        'amount': 10000,
        'type': 'expense',
        'timestamp': '2025-06-01T12:00:00',
        **kwargs,
    }
    return client.post('/api/transactions', json=payload)


def test_list_empty(auth_client):
    res = auth_client.get('/api/transactions')
    assert res.status_code == 200
    data = res.get_json()
    assert data['total'] == 0
    assert data['items'] == []


def test_create_expense(auth_client):
    res = _create_manual(auth_client, amount=5000, type='expense')
    assert res.status_code == 201
    data = res.get_json()
    assert data['amount'] == -5000
    assert data['transaction_type'] == 'expense'
    assert data['is_manual'] is True


def test_create_income(auth_client):
    res = _create_manual(auth_client, amount=20000, type='income')
    assert res.status_code == 201
    data = res.get_json()
    assert data['amount'] == 20000
    assert data['transaction_type'] == 'income'


def test_pagination(auth_client):
    for i in range(5):
        _create_manual(auth_client, description=f'tx{i}')

    res = auth_client.get('/api/transactions?page=1&per_page=3')
    data = res.get_json()
    assert data['total'] == 5
    assert len(data['items']) == 3
    assert data['pages'] == 2


def test_filter_by_type(auth_client):
    _create_manual(auth_client, type='income', amount=1000)
    _create_manual(auth_client, type='expense', amount=2000)
    _create_manual(auth_client, type='expense', amount=3000)

    res = auth_client.get('/api/transactions?type=expense')
    data = res.get_json()
    assert data['total'] == 2
    assert all(t['transaction_type'] == 'expense' for t in data['items'])


def test_filter_by_date(auth_client):
    _create_manual(auth_client, timestamp='2025-01-15T10:00:00')
    _create_manual(auth_client, timestamp='2025-06-15T10:00:00')

    res = auth_client.get('/api/transactions?from=2025-06-01&to=2025-06-30')
    data = res.get_json()
    assert data['total'] == 1


def test_update_category(auth_client, db):
    from app.models import Category
    cat = Category(name='Food', user_id=None, is_default=False)
    db.session.add(cat)
    db.session.commit()

    res = _create_manual(auth_client)
    tx_id = res.get_json()['id']

    res = auth_client.put(f'/api/transactions/{tx_id}', json={'category_id': cat.id})
    assert res.status_code == 200
    assert res.get_json()['category_id'] == cat.id


def test_delete_manual(auth_client):
    res = _create_manual(auth_client)
    tx_id = res.get_json()['id']

    res = auth_client.delete(f'/api/transactions/{tx_id}')
    assert res.status_code == 200

    res = auth_client.get('/api/transactions')
    assert res.get_json()['total'] == 0


def test_cannot_delete_non_manual(auth_client, db):
    me = auth_client.get('/api/auth/me').get_json()
    tx = Transaction(
        user_id=me['id'],
        amount=-5000,
        transaction_type='expense',
        timestamp=datetime(2025, 6, 1),
        is_manual=False,
        external_id='monobank-123',
    )
    db.session.add(tx)
    db.session.commit()

    res = auth_client.delete(f'/api/transactions/{tx.id}')
    assert res.status_code == 403


def test_cannot_access_other_user_transaction(client, db):
    from app.models import User, Transaction

    other = User(email='other@test.com')
    other.set_password('password123')
    db.session.add(other)
    db.session.flush()

    tx = Transaction(
        user_id=other.id,
        amount=-1000,
        transaction_type='expense',
        timestamp=datetime(2025, 6, 1),
        is_manual=True,
    )
    db.session.add(tx)
    db.session.commit()

    # Login as a different user
    client.post('/api/auth/register', json={'email': 'me@test.com', 'password': 'password123'})
    client.post('/api/auth/login', json={'email': 'me@test.com', 'password': 'password123'})

    res = client.delete(f'/api/transactions/{tx.id}')
    assert res.status_code == 404
