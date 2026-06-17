from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import Account, Transaction
from ..services.monobank import MonobankConnector, MonobankAPIError
from ..utils.encryption import encrypt_token

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')


@accounts_bp.route('', methods=['GET'])
@jwt_required()
def list_accounts():
    user_id = int(get_jwt_identity())
    accounts = db.session.scalars(db.select(Account).filter_by(user_id=user_id)).all()
    return jsonify([a.to_dict() for a in accounts])


@accounts_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    bank_type = data.get('bank_type', 'monobank')
    token = data.get('token', '').strip()

    if bank_type != 'monobank' or not token:
        return jsonify({'error': 'bank_type must be "monobank" and token is required'}), 422

    try:
        connector = MonobankConnector(token)
        client_info = connector.get_client_info()
    except MonobankAPIError as e:
        return jsonify({'error': f'Monobank API error: {str(e)}'}), 400

    encrypted = encrypt_token(token)
    created = []

    for acc in client_info.get('accounts', []):
        already_exists = db.session.scalar(
            db.select(Account).filter_by(user_id=user_id, bank_account_id=acc['id'])
        )
        if already_exists:
            continue

        account = Account(
            user_id=user_id,
            bank_type='monobank',
            encrypted_token=encrypted,
            bank_account_id=acc['id'],
            currency_code=acc.get('currencyCode', 980),
            balance=acc.get('balance', 0),
        )
        db.session.add(account)
        db.session.flush()
        created.append(account)

    db.session.commit()

    webhook_secret = current_app.config.get('WEBHOOK_SECRET', '')
    webhook_base = current_app.config.get('WEBHOOK_BASE_URL', '')
    if webhook_base and webhook_secret:
        webhook_url = f'{webhook_base}/api/webhooks/monobank?secret={webhook_secret}'
        connector.setup_webhook(webhook_url)

    from ..services.importer import import_account_transactions
    for account in created:
        import_account_transactions.delay(account.id)

    return jsonify([a.to_dict() for a in created]), 201


@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    user_id = int(get_jwt_identity())
    account = db.session.get(Account, account_id)

    if not account or account.user_id != user_id:
        return jsonify({'error': 'Account not found'}), 404

    # Keep transactions but detach them from the account
    db.session.execute(
        db.update(Transaction)
        .where(Transaction.account_id == account_id)
        .values(account_id=None)
    )
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Account disconnected'}), 200


@accounts_bp.route('/<int:account_id>/sync', methods=['POST'])
@jwt_required()
def sync_account(account_id):
    user_id = int(get_jwt_identity())
    account = db.session.get(Account, account_id)

    if not account or account.user_id != user_id:
        return jsonify({'error': 'Account not found'}), 404

    from ..services.importer import import_account_transactions
    task = import_account_transactions.delay(account.id, months=1)

    return jsonify({'message': 'Sync started', 'task_id': task.id}), 202
