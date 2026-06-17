from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest
from app.models import Account, Category, Budget, Notification
from app.utils.encryption import encrypt_token


@pytest.fixture
def account(db, auth_client):
    me = auth_client.get('/api/auth/me').get_json()
    acc = Account(
        user_id=me['id'],
        bank_type='monobank',
        encrypted_token=encrypt_token('tok'),
        bank_account_id='webhook-acc',
        currency_code=980,
        balance=0,
    )
    db.session.add(acc)
    db.session.commit()
    return acc


def _statement_item(tx_id='tx-1', amount=-5000, mcc=5411, ts=1700000000):
    return {
        'id': tx_id,
        'time': ts,
        'amount': amount,
        'mcc': mcc,
        'description': 'ATB Market',
        'currencyCode': 980,
        'balance': 95000,
    }


def _webhook_payload(account, item):
    return {
        'type': 'StatementItem',
        'data': {
            'account': account.bank_account_id,
            'statementItem': item,
        },
    }


def test_webhook_wrong_secret(client, account):
    res = client.post(
        '/api/webhooks/monobank?secret=wrong-secret',
        json=_webhook_payload(account, _statement_item()),
    )
    assert res.status_code == 401


def test_webhook_missing_secret(client, account):
    res = client.post(
        '/api/webhooks/monobank',
        json=_webhook_payload(account, _statement_item()),
    )
    assert res.status_code == 401


def test_webhook_non_statement_type(client):
    res = client.post(
        '/api/webhooks/monobank?secret=test-secret',
        json={'type': 'SomethingElse', 'data': {}},
    )
    assert res.status_code == 200
    assert res.get_json()['ok'] is True


def test_webhook_empty_payload(client):
    res = client.post('/api/webhooks/monobank?secret=test-secret', json={})
    assert res.status_code == 200


def test_webhook_unknown_account(client):
    payload = {
        'type': 'StatementItem',
        'data': {
            'account': 'does-not-exist',
            'statementItem': _statement_item(),
        },
    }
    res = client.post('/api/webhooks/monobank?secret=test-secret', json=payload)
    assert res.status_code == 200
    assert res.get_json()['ok'] is True


def test_webhook_creates_transaction(client, db, account):
    default_cat = Category(name='Інше', user_id=None, is_default=True)
    db.session.add(default_cat)
    db.session.commit()

    item = _statement_item()
    res = client.post(
        '/api/webhooks/monobank?secret=test-secret',
        json=_webhook_payload(account, item),
    )
    assert res.status_code == 200

    from app.models import Transaction
    tx = db.session.scalar(
        db.select(Transaction).filter_by(external_id='tx-1')
    )
    assert tx is not None
    assert tx.amount == -5000
    assert tx.transaction_type == 'expense'
    assert tx.account_id == account.id


def test_webhook_deduplicates_transactions(client, db, account):
    default_cat = Category(name='Інше', user_id=None, is_default=True)
    db.session.add(default_cat)
    db.session.commit()

    item = _statement_item(tx_id='dup-tx')
    payload = _webhook_payload(account, item)

    client.post('/api/webhooks/monobank?secret=test-secret', json=payload)
    client.post('/api/webhooks/monobank?secret=test-secret', json=payload)

    from app.models import Transaction
    count = db.session.scalar(
        db.select(db.func.count(Transaction.id)).filter_by(external_id='dup-tx')
    )
    assert count == 1


def test_webhook_budget_exceeded_notification(client, db, account):
    me_id = account.user_id

    default_cat = Category(name='Їжа', user_id=None, is_default=True)
    db.session.add(default_cat)
    db.session.flush()

    budget = Budget(
        user_id=me_id,
        category_id=default_cat.id,
        month='2023-11',
        planned_amount=5000,
    )
    db.session.add(budget)
    db.session.commit()

    # Timestamp in November 2023 → month matches budget
    item = _statement_item(
        tx_id='over-budget',
        amount=-5000,
        mcc=0,
        ts=1700000000,  # 2023-11-14
    )

    # Force category_id to match the budget category via mock
    from app.models import Transaction
    from datetime import datetime, timezone

    with patch('app.services.categorizer.TransactionCategorizer.categorize',
               return_value=default_cat.id):
        client.post(
            '/api/webhooks/monobank?secret=test-secret',
            json=_webhook_payload(account, item),
        )

    notif = db.session.scalar(
        db.select(Notification).filter_by(user_id=me_id)
    )
    assert notif is not None
    assert notif.type in ('budget_warning', 'budget_exceeded')
    assert 'Їжа' in notif.message


def test_webhook_no_notification_below_threshold(client, db, account):
    me_id = account.user_id

    default_cat = Category(name='Інше', user_id=None, is_default=True)
    db.session.add(default_cat)
    db.session.flush()

    budget = Budget(
        user_id=me_id,
        category_id=default_cat.id,
        month='2023-11',
        planned_amount=1000000,  # Very large budget → small tx won't trigger
    )
    db.session.add(budget)
    db.session.commit()

    item = _statement_item(tx_id='small-tx', amount=-100, ts=1700000000)

    with patch('app.services.categorizer.TransactionCategorizer.categorize',
               return_value=default_cat.id):
        client.post(
            '/api/webhooks/monobank?secret=test-secret',
            json=_webhook_payload(account, item),
        )

    count = db.session.scalar(
        db.select(db.func.count(Notification.id)).filter_by(user_id=me_id)
    )
    assert count == 0
