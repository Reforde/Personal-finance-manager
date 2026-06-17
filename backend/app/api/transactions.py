from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import func

from ..extensions import db
from ..models import Category, Transaction
from ..utils.validators import TransactionCreateSchema, TransactionUpdateSchema
from ..services.budget_notifications import check_budget

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

_create_schema = TransactionCreateSchema()
_update_schema = TransactionUpdateSchema()


def _tx_dict(tx: Transaction) -> dict:
    data = tx.to_dict()
    if tx.category:
        data['category'] = {
            'id': tx.category.id,
            'name': tx.category.name,
            'icon': tx.category.icon,
        }
    return data


def _build_filters(user_id: int) -> list:
    filters = [Transaction.user_id == user_id]

    raw_from = request.args.get('from')
    raw_to = request.args.get('to')
    category_id = request.args.get('category_id', type=int)
    tx_type = request.args.get('type', 'all')
    min_amount = request.args.get('min_amount', type=int)
    max_amount = request.args.get('max_amount', type=int)

    if raw_from:
        try:
            filters.append(Transaction.timestamp >= datetime.fromisoformat(raw_from))
        except ValueError:
            pass
    if raw_to:
        try:
            filters.append(Transaction.timestamp <= datetime.fromisoformat(raw_to))
        except ValueError:
            pass
    if category_id is not None:
        filters.append(Transaction.category_id == category_id)
    if tx_type in ('income', 'expense'):
        filters.append(Transaction.transaction_type == tx_type)
    if min_amount is not None:
        filters.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        filters.append(Transaction.amount <= max_amount)

    return filters


@transactions_bp.route('', methods=['GET'])
@jwt_required()
def list_transactions():
    user_id = int(get_jwt_identity())
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    filters = _build_filters(user_id)

    total = db.session.scalar(
        db.select(func.count(Transaction.id)).where(*filters)
    )
    items = db.session.scalars(
        db.select(Transaction)
        .where(*filters)
        .order_by(Transaction.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    return jsonify({
        'items': [_tx_dict(t) for t in items],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': max((total + per_page - 1) // per_page, 1),
    })


@transactions_bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    user_id = int(get_jwt_identity())

    try:
        data = _create_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    if data['category_id'] is not None:
        category = db.session.get(Category, data['category_id'])
        if not category or (category.user_id is not None and category.user_id != user_id):
            return jsonify({'error': 'Category not found'}), 404

    # Enforce sign convention: expense → negative, income → positive
    amount = abs(data['amount'])
    if data['transaction_type'] == 'expense':
        amount = -amount

    tx = Transaction(
        user_id=user_id,
        account_id=None,
        amount=amount,
        description=data['description'],
        category_id=data['category_id'],
        transaction_type=data['transaction_type'],
        currency_code=data['currency_code'],
        timestamp=data['timestamp'],
        is_manual=True,
    )
    db.session.add(tx)
    db.session.flush()
    check_budget(tx)
    db.session.commit()
    return jsonify(_tx_dict(tx)), 201


@transactions_bp.route('/<int:tx_id>', methods=['PUT'])
@jwt_required()
def update_transaction(tx_id):
    user_id = int(get_jwt_identity())
    tx = db.session.get(Transaction, tx_id)

    if not tx or tx.user_id != user_id:
        return jsonify({'error': 'Transaction not found'}), 404

    try:
        data = _update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    category = db.session.get(Category, data['category_id'])
    if not category or (category.user_id is not None and category.user_id != user_id):
        return jsonify({'error': 'Category not found'}), 404

    tx.category_id = data['category_id']
    db.session.commit()
    return jsonify(_tx_dict(tx))


@transactions_bp.route('/<int:tx_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(tx_id):
    user_id = int(get_jwt_identity())
    tx = db.session.get(Transaction, tx_id)

    if not tx or tx.user_id != user_id:
        return jsonify({'error': 'Transaction not found'}), 404
    if not tx.is_manual:
        return jsonify({'error': 'Only manual transactions can be deleted'}), 403

    db.session.delete(tx)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted'}), 200
