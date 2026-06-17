from ..extensions import db


class MonthlyBalance(db.Model):
    __tablename__ = 'monthly_balances'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    amount = db.Column(db.BigInteger, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', name='uq_monthly_balance_user_month'),
    )

    def to_dict(self):
        return {'month': self.month, 'amount': self.amount}
