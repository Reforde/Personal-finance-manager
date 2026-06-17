from ..extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = системна
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    is_default = db.Column(db.Boolean, default=False)

    children = db.relationship(
        'Category',
        backref=db.backref('parent', remote_side=[id]),
        lazy=True,
    )
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    mcc_mappings = db.relationship('MCCMapping', backref='category', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='category', lazy=True)

    def to_dict(self, include_children=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'icon': self.icon,
            'is_default': self.is_default,
        }
        if include_children:
            data['children'] = [c.to_dict() for c in self.children]
        return data


class MCCMapping(db.Model):
    __tablename__ = 'mcc_mappings'

    id = db.Column(db.Integer, primary_key=True)
    mcc_code = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description_pattern = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('ix_mcc_mappings_mcc_code', 'mcc_code'),
    )
