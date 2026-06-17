from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    items = db.session.scalars(
        db.select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return jsonify([n.to_dict() for n in items])


@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notif_id):
    user_id = int(get_jwt_identity())
    notif = db.session.get(Notification, notif_id)
    if not notif or notif.user_id != user_id:
        return jsonify({'error': 'Not found'}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify(notif.to_dict())


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    db.session.execute(
        db.update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.session.commit()
    return jsonify({'ok': True})
