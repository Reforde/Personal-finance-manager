from ..extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    external_id = db.Column(db.String(255), unique=True, nullable=True)
    amount = db.Column(db.BigInteger, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    mcc_code = db.Column(db.Integer, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'income' / 'expense'
    currency_code = db.Column(db.Integer, nullable=False, default=980)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_manual = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('ix_transactions_user_timestamp', 'user_id', 'timestamp'),
        db.Index('ix_transactions_external_id', 'external_id'),
        db.Index('ix_transactions_category_id', 'category_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'external_id': self.external_id,
            'amount': self.amount,
            'description': self.description,
            'mcc_code': self.mcc_code,
            'category_id': self.category_id,
            'transaction_type': self.transaction_type,
            'currency_code': self.currency_code,
            'timestamp': self.timestamp.isoformat(),
            'is_manual': self.is_manual,
        }
