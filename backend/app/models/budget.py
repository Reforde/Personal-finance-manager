from ..extensions import db


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # "2025-06"
    planned_amount = db.Column(db.BigInteger, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', 'month', name='uq_budget_user_category_month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'month': self.month,
            'planned_amount': self.planned_amount,
        }
