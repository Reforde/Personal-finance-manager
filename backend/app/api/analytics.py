import re
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services import analytics as svc

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

_MONTH_RE = re.compile(r'^\d{4}-\d{2}$')


def _parse_dt(value: str | None, fallback: datetime) -> datetime:
    try:
        return datetime.fromisoformat(value) if value else fallback
    except ValueError:
        return fallback


def _month_start() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


@analytics_bp.route('/spending-by-category', methods=['GET'])
@jwt_required()
def spending_by_category():
    user_id = int(get_jwt_identity())
    from_dt = _parse_dt(request.args.get('from'), _month_start())
    to_dt = _parse_dt(request.args.get('to'), datetime.utcnow())
    return jsonify(svc.spending_by_category(user_id, from_dt, to_dt))


@analytics_bp.route('/monthly-trend', methods=['GET'])
@jwt_required()
def monthly_trend():
    user_id = int(get_jwt_identity())
    months = min(max(request.args.get('months', 12, type=int), 1), 24)
    return jsonify(svc.monthly_trend(user_id, months))


@analytics_bp.route('/daily-heatmap', methods=['GET'])
@jwt_required()
def daily_heatmap():
    user_id = int(get_jwt_identity())
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))

    if not _MONTH_RE.match(month):
        return jsonify({'error': 'month must be in YYYY-MM format'}), 422

    return jsonify(svc.daily_heatmap(user_id, month))


@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    user_id = int(get_jwt_identity())
    from_dt = _parse_dt(request.args.get('from'), _month_start())
    to_dt = _parse_dt(request.args.get('to'), datetime.utcnow())
    return jsonify(svc.summary(user_id, from_dt, to_dt))
