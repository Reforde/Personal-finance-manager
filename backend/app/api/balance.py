import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import MonthlyBalance

balance_bp = Blueprint('balance', __name__, url_prefix='/api/balance')

_MONTH_RE = re.compile(r'^\d{4}-\d{2}$')


@balance_bp.route('/<month>', methods=['GET'])
@jwt_required()
def get_balance(month):
    if not _MONTH_RE.match(month):
        return jsonify({'error': 'month must be YYYY-MM'}), 422

    user_id = int(get_jwt_identity())
    record = db.session.scalar(
        db.select(MonthlyBalance).where(
            MonthlyBalance.user_id == user_id,
            MonthlyBalance.month == month,
        )
    )
    return jsonify({'month': month, 'amount': record.amount if record else 0})


@balance_bp.route('/<month>', methods=['PUT'])
@jwt_required()
def set_balance(month):
    if not _MONTH_RE.match(month):
        return jsonify({'error': 'month must be YYYY-MM'}), 422

    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    try:
        amount = int(data['amount'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'amount must be an integer (kopecks)'}), 422

    record = db.session.scalar(
        db.select(MonthlyBalance).where(
            MonthlyBalance.user_id == user_id,
            MonthlyBalance.month == month,
        )
    )
    if record:
        record.amount = amount
    else:
        record = MonthlyBalance(user_id=user_id, month=month, amount=amount)
        db.session.add(record)

    db.session.commit()
    return jsonify(record.to_dict())
