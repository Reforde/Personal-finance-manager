from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from marshmallow import ValidationError

from ..extensions import db
from ..models import User
from ..utils.validators import RegisterSchema, LoginSchema

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

_register_schema = RegisterSchema()
_login_schema = LoginSchema()


def _auth_response(user, status_code=200):
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    response = make_response(jsonify(user.to_dict()), status_code)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = _register_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    if db.session.scalar(db.select(User).filter_by(email=data['email'])):
        return jsonify({'error': 'Email already registered'}), 409

    user = User(email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return _auth_response(user, 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = _login_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    user = db.session.scalar(db.select(User).filter_by(email=data['email']))
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    return _auth_response(user)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    access_token = create_access_token(identity=str(user_id))
    response = make_response(jsonify({'message': 'Token refreshed'}))
    set_access_cookies(response, access_token)
    return response


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out'}))
    unset_jwt_cookies(response)
    return response


@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    user = db.session.get(User, int(get_jwt_identity()))
    data = request.get_json() or {}

    current = data.get('current_password', '')
    new = data.get('new_password', '')

    if not user.check_password(current):
        return jsonify({'error': 'Поточний пароль невірний'}), 400
    if len(new) < 8:
        return jsonify({'error': 'Новий пароль має бути мінімум 8 символів'}), 422

    user.set_password(new)
    db.session.commit()
    return jsonify({'message': 'Password changed'})


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    data = request.get_json() or {}

    currency = data.get('default_currency')
    if currency and currency in ('UAH', 'USD', 'EUR'):
        user.default_currency = currency

    if 'manual_balance' in data:
        try:
            user.manual_balance = int(data['manual_balance'])
        except (ValueError, TypeError):
            pass

    db.session.commit()
    return jsonify(user.to_dict())
