from datetime import datetime, timezone
import bcrypt
from ..extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    default_currency = db.Column(db.String(3), default='UAH')
    manual_balance = db.Column(db.BigInteger, default=0, nullable=False, server_default='0')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'default_currency': self.default_currency,
            'manual_balance': self.manual_balance,
            'created_at': self.created_at.isoformat(),
        }
