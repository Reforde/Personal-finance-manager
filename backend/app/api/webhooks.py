import hmac

from flask import Blueprint, request, jsonify, current_app

from ..extensions import db
from ..models import Account, Transaction
from ..services.importer import process_statement_item
from ..services.budget_notifications import check_budget

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')


@webhooks_bp.route('/monobank', methods=['POST'])
def monobank_webhook():
    secret = request.args.get('secret', '')
    expected = current_app.config.get('WEBHOOK_SECRET', '')

    if not hmac.compare_digest(secret, expected):
        return jsonify({'error': 'Unauthorized'}), 401

    payload = request.get_json(silent=True)
    if not payload or payload.get('type') != 'StatementItem':
        return jsonify({'ok': True}), 200

    bank_account_id = payload.get('data', {}).get('account')
    statement_item = payload.get('data', {}).get('statementItem')
    if not bank_account_id or not statement_item:
        return jsonify({'ok': True}), 200

    account = db.session.scalar(
        db.select(Account).filter_by(bank_account_id=bank_account_id)
    )
    if not account:
        return jsonify({'ok': True}), 200

    tx = process_statement_item(account, statement_item)
    if tx:
        db.session.flush()
        check_budget(tx)
        db.session.commit()

    return jsonify({'ok': True}), 200
