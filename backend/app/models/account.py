from ..extensions import db


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bank_type = db.Column(db.String(50), nullable=False, default='monobank')
    encrypted_token = db.Column(db.Text, nullable=False)
    bank_account_id = db.Column(db.String(255), nullable=False)
    currency_code = db.Column(db.Integer, nullable=False, default=980)
    balance = db.Column(db.BigInteger, default=0)
    last_sync_at = db.Column(db.DateTime, nullable=True)

    transactions = db.relationship('Transaction', backref='account', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bank_type': self.bank_type,
            'bank_account_id': self.bank_account_id,
            'currency_code': self.currency_code,
            'balance': self.balance,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
        }
