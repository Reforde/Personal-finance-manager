from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from ..extensions import db
from ..models import Category, Transaction, Budget
from ..utils.validators import CategorySchema, CategoryUpdateSchema

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

_create_schema = CategorySchema()
_update_schema = CategoryUpdateSchema()


def _build_tree(categories: list, parent_id=None) -> list:
    return [
        {**c.to_dict(), 'children': _build_tree(categories, c.id)}
        for c in categories
        if c.parent_id == parent_id
    ]


@categories_bp.route('', methods=['GET'])
@jwt_required()
def list_categories():
    user_id = int(get_jwt_identity())

    categories = db.session.scalars(
        db.select(Category)
        .where(
            db.or_(Category.user_id.is_(None), Category.user_id == user_id)
        )
        .order_by(Category.name)
    ).all()

    return jsonify(_build_tree(categories))


@categories_bp.route('', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())

    try:
        data = _create_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    # Validate parent belongs to this user or is a system category
    if data['parent_id'] is not None:
        parent = db.session.get(Category, data['parent_id'])
        if not parent or (parent.user_id is not None and parent.user_id != user_id):
            return jsonify({'error': 'Parent category not found'}), 404

    category = Category(
        user_id=user_id,
        name=data['name'],
        parent_id=data['parent_id'],
        icon=data['icon'],
        is_default=False,
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    user_id = int(get_jwt_identity())
    category = db.session.get(Category, category_id)

    if not category or category.user_id != user_id:
        return jsonify({'error': 'Category not found'}), 404

    try:
        data = _update_schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422

    if 'name' in data:
        category.name = data['name']
    if 'icon' in data:
        category.icon = data['icon']

    db.session.commit()
    return jsonify(category.to_dict())


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    user_id = int(get_jwt_identity())
    category = db.session.get(Category, category_id)

    if not category or category.user_id != user_id:
        return jsonify({'error': 'Category not found'}), 404

    default_id = db.session.scalar(
        db.select(Category.id).filter_by(is_default=True, user_id=None)
    )

    # Re-assign related records to the default category
    db.session.execute(
        db.update(Transaction)
        .where(Transaction.category_id == category_id)
        .values(category_id=default_id)
    )
    db.session.execute(
        db.update(Budget)
        .where(Budget.category_id == category_id)
        .values(category_id=default_id)
    )

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted'}), 200
