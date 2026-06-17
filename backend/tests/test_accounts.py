from unittest.mock import patch, MagicMock

import pytest


def _client_info():
    return {
        'clientId': 'test-client',
        'name': 'Test User',
        'accounts': [
            {'id': 'acc-uah', 'currencyCode': 980, 'balance': 100000},
            {'id': 'acc-usd', 'currencyCode': 840, 'balance': 5000},
        ],
    }


def _make_account(db, auth_client):
    from app.models import Account
    from app.utils.encryption import encrypt_token

    me = auth_client.get('/api/auth/me').get_json()
    account = Account(
        user_id=me['id'],
        bank_type='monobank',
        encrypted_token=encrypt_token('test-token'),
        bank_account_id='acc-direct',
        currency_code=980,
        balance=0,
    )
    db.session.add(account)
    db.session.commit()
    return account


def test_list_accounts_empty(auth_client):
    res = auth_client.get('/api/accounts')
    assert res.status_code == 200
    assert res.get_json() == []


def test_connect_monobank_success(auth_client):
    with patch('app.api.accounts.MonobankConnector') as MockCls, \
         patch('app.services.importer.import_account_transactions') as mock_task:

        mock_conn = MagicMock()
        mock_conn.get_client_info.return_value = _client_info()
        mock_conn.setup_webhook.return_value = True
        MockCls.return_value = mock_conn

        task_mock = MagicMock()
        task_mock.id = 'fake-task-id'
        mock_task.delay.return_value = task_mock

        res = auth_client.post('/api/accounts/connect', json={
            'bank_type': 'monobank',
            'token': 'valid-token',
        })

    assert res.status_code == 201
    accounts = res.get_json()
    assert len(accounts) == 2
    assert all(a['bank_type'] == 'monobank' for a in accounts)
    bank_ids = [a['bank_account_id'] for a in accounts]
    assert 'acc-uah' in bank_ids
    assert 'acc-usd' in bank_ids


def test_connect_stores_accounts_in_db(auth_client):
    with patch('app.api.accounts.MonobankConnector') as MockCls, \
         patch('app.services.importer.import_account_transactions') as mock_task:

        mock_conn = MagicMock()
        mock_conn.get_client_info.return_value = _client_info()
        MockCls.return_value = mock_conn
        mock_task.delay.return_value = MagicMock(id='t1')

        auth_client.post('/api/accounts/connect', json={
            'bank_type': 'monobank',
            'token': 'valid-token',
        })

    res = auth_client.get('/api/accounts')
    assert len(res.get_json()) == 2


def test_connect_invalid_bank_type(auth_client):
    res = auth_client.post('/api/accounts/connect', json={
        'bank_type': 'privatbank',
        'token': 'some-token',
    })
    assert res.status_code == 422


def test_connect_missing_token(auth_client):
    res = auth_client.post('/api/accounts/connect', json={'bank_type': 'monobank'})
    assert res.status_code == 422


def test_connect_empty_token(auth_client):
    res = auth_client.post('/api/accounts/connect', json={
        'bank_type': 'monobank',
        'token': '   ',
    })
    assert res.status_code == 422


def test_connect_monobank_api_error(auth_client):
    from app.services.monobank import MonobankAPIError

    with patch('app.api.accounts.MonobankConnector') as MockCls:
        mock_conn = MagicMock()
        mock_conn.get_client_info.side_effect = MonobankAPIError('Unauthorized')
        MockCls.return_value = mock_conn

        res = auth_client.post('/api/accounts/connect', json={
            'bank_type': 'monobank',
            'token': 'bad-token',
        })

    assert res.status_code == 400
    assert 'error' in res.get_json()


def test_connect_no_duplicates(auth_client):
    with patch('app.api.accounts.MonobankConnector') as MockCls, \
         patch('app.services.importer.import_account_transactions') as mock_task:

        mock_conn = MagicMock()
        mock_conn.get_client_info.return_value = _client_info()
        MockCls.return_value = mock_conn
        mock_task.delay.return_value = MagicMock(id='t1')

        # first connect
        auth_client.post('/api/accounts/connect', json={'bank_type': 'monobank', 'token': 'tok'})
        # second connect with same token / same accounts
        res = auth_client.post('/api/accounts/connect', json={'bank_type': 'monobank', 'token': 'tok'})

    assert res.status_code == 201
    assert res.get_json() == []  # all accounts already exist → nothing created


def test_delete_account(auth_client, db):
    account = _make_account(db, auth_client)

    res = auth_client.delete(f'/api/accounts/{account.id}')
    assert res.status_code == 200
    assert 'message' in res.get_json()

    res = auth_client.get('/api/accounts')
    assert res.get_json() == []


def test_delete_account_keeps_transactions(auth_client, db):
    from app.models import Transaction
    from datetime import datetime

    account = _make_account(db, auth_client)
    me = auth_client.get('/api/auth/me').get_json()

    tx = Transaction(
        user_id=me['id'],
        account_id=account.id,
        amount=-1000,
        transaction_type='expense',
        timestamp=datetime(2025, 6, 1),
        is_manual=False,
        external_id='keep-me',
    )
    db.session.add(tx)
    db.session.commit()

    auth_client.delete(f'/api/accounts/{account.id}')

    tx_reloaded = db.session.get(Transaction, tx.id)
    assert tx_reloaded is not None
    assert tx_reloaded.account_id is None


def test_delete_account_not_found(auth_client):
    res = auth_client.delete('/api/accounts/99999')
    assert res.status_code == 404


def test_delete_other_users_account(client, db):
    from app.models import Account, User
    from app.utils.encryption import encrypt_token

    other = User(email='other2@test.com')
    other.set_password('password123')
    db.session.add(other)
    db.session.flush()

    account = Account(
        user_id=other.id,
        bank_type='monobank',
        encrypted_token=encrypt_token('tok'),
        bank_account_id='other-acc',
        currency_code=980,
        balance=0,
    )
    db.session.add(account)
    db.session.commit()

    client.post('/api/auth/register', json={'email': 'me2@test.com', 'password': 'password123'})
    client.post('/api/auth/login', json={'email': 'me2@test.com', 'password': 'password123'})

    res = client.delete(f'/api/accounts/{account.id}')
    assert res.status_code == 404


def test_sync_account(auth_client, db):
    account = _make_account(db, auth_client)

    with patch('app.services.importer.import_account_transactions') as mock_task:
        mock_task.delay.return_value = MagicMock(id='sync-task-id')
        res = auth_client.post(f'/api/accounts/{account.id}/sync')

    assert res.status_code == 202
    data = res.get_json()
    assert data['message'] == 'Sync started'
    assert 'task_id' in data


def test_sync_account_not_found(auth_client):
    res = auth_client.post('/api/accounts/99999/sync')
    assert res.status_code == 404


def test_accounts_unauthenticated(client):
    assert client.get('/api/accounts').status_code == 401
    assert client.post('/api/accounts/connect', json={}).status_code == 401
    assert client.delete('/api/accounts/1').status_code == 401
    assert client.post('/api/accounts/1/sync').status_code == 401
