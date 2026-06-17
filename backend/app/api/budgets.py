from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import func

from ..extensions import db
from ..models import Budget, Category, Transaction
from ..utils.validators import BudgetCreateSchema, BudgetUpdateSchema, BudgetCopySchema

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

_create_schema = BudgetCreateSchema()
_update_schema = BudgetUpdateSchema()
_copy_schema = BudgetCopySchema()


def _month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(month + '-01', '%Y-%m-%d')
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end


def _get_spent(user_id: int, category_id: int, month: str) -> int:
    start, end = _month_bounds(month)
    result = db.session.scalar(
        db.select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_type == 'expense',
            Transaction.timestamp >= start,
            Transaction.timestamp < end,
        )
    )
    return abs(result or 0)


def _budget_dict(budget: Budget, user_id: int) -> dict:
    spent = _get_spent(user_id, budget.category_id, budget.month)
    remaining = budget.planned_amount - spent
    progress = round(spent / budget.planned_amount, 4) if budget.planned_amount else 0.0

    data = budget.to_dict()
    data['spent'] = spent
    data['remaining'] = remaining
    data['progress'] = progress

    if budget.category:
        data['category'] = {
            'id': budget.category.id,
            'name': budget.category.name,
            'icon': budget.category.icon,
        }

    return data


def _current_month() -> str:
    return datetime.utcnow().strftime('%Y-%m')


@budgets_bp.route('', methods=['GET'])
@jwt_required()
def list_budgets():
    user_id = int(get_jwt_identity())
    month = request.args.get('month', _current_month())

    budgets = db.session.scalars(
        db.select(Budget)
        .where(Budget.user_id == user_id, Budget.month == month)
        .order_by(Budget.id)
    ).all()

    return jsonify([_budget_dict(b, user_id) for b in budgets])


@budgets_bp.route('', methods=['POST'])
@jwt_required()
def create_budget():
    user_id = int(get_jwt_identity())

    try:
        data = _create_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    category = db.session.get(Category, data['category_id'])
    if not category or (category.user_id is not None and category.user_id != user_id):
        return jsonify({'error': 'Category not found'}), 404

    existing = db.session.scalar(
        db.select(Budget).filter_by(
            user_id=user_id,
            category_id=data['category_id'],
            month=data['month'],
        )
    )
    if existing:
        return jsonify({'error': 'Budget for this category and month already exists'}), 409

    budget = Budget(
        user_id=user_id,
        category_id=data['category_id'],
        month=data['month'],
        planned_amount=data['planned_amount'],
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify(_budget_dict(budget, user_id)), 201


@budgets_bp.route('/copy', methods=['POST'])
@jwt_required()
def copy_budgets():
    user_id = int(get_jwt_identity())

    try:
        data = _copy_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    from_month = data['from_month']
    to_month = data['to_month']

    if from_month == to_month:
        return jsonify({'error': 'from_month and to_month must be different'}), 422

    source_budgets = db.session.scalars(
        db.select(Budget).filter_by(user_id=user_id, month=from_month)
    ).all()

    if not source_budgets:
        return jsonify({'error': f'No budgets found for {from_month}'}), 404

    created = []
    for source in source_budgets:
        already_exists = db.session.scalar(
            db.select(Budget).filter_by(
                user_id=user_id,
                category_id=source.category_id,
                month=to_month,
            )
        )
        if already_exists:
            continue

        budget = Budget(
            user_id=user_id,
            category_id=source.category_id,
            month=to_month,
            planned_amount=source.planned_amount,
        )
        db.session.add(budget)
        db.session.flush()
        created.append(budget)

    db.session.commit()
    return jsonify([_budget_dict(b, user_id) for b in created]), 201


@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    user_id = int(get_jwt_identity())
    budget = db.session.get(Budget, budget_id)

    if not budget or budget.user_id != user_id:
        return jsonify({'error': 'Budget not found'}), 404

    try:
        data = _update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    budget.planned_amount = data['planned_amount']
    db.session.commit()
    return jsonify(_budget_dict(budget, user_id))


@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    user_id = int(get_jwt_identity())
    budget = db.session.get(Budget, budget_id)

    if not budget or budget.user_id != user_id:
        return jsonify({'error': 'Budget not found'}), 404

    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted'}), 200
