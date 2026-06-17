import re
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from ..services.privatbank import PrivatBankConnector, PrivatBankAPIError, get_redis_client

rates_bp = Blueprint('rates', __name__, url_prefix='/api/rates')

_DATE_RE = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')


def _connector() -> PrivatBankConnector:
    redis_url = current_app.config.get('REDIS_URL')
    client = get_redis_client(redis_url) if redis_url else None
    return PrivatBankConnector(redis_client=client)


@rates_bp.route('/current', methods=['GET'])
@jwt_required()
def current_rates():
    try:
        rates = _connector().get_current_rates()
    except PrivatBankAPIError as e:
        return jsonify({'error': str(e)}), 503
    return jsonify(rates)


@rates_bp.route('/archive', methods=['GET'])
@jwt_required()
def archive_rates():
    date = request.args.get('date', '').strip()
    if not date or not _DATE_RE.match(date):
        return jsonify({'error': 'date is required in DD.MM.YYYY format'}), 422

    try:
        rates = _connector().get_archive_rates(date)
    except PrivatBankAPIError as e:
        return jsonify({'error': str(e)}), 503
    return jsonify(rates)
