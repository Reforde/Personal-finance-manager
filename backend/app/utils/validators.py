from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class CategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    parent_id = fields.Int(load_default=None)
    icon = fields.Str(load_default=None, validate=validate.Length(max=50))


class CategoryUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    icon = fields.Str(validate=validate.Length(max=50))


class TransactionCreateSchema(Schema):
    amount = fields.Int(required=True)
    description = fields.Str(load_default='', validate=validate.Length(max=500))
    category_id = fields.Int(load_default=None)
    timestamp = fields.DateTime(required=True)
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(['income', 'expense']),
        data_key='type',
    )
    currency_code = fields.Int(load_default=980)


class TransactionUpdateSchema(Schema):
    category_id = fields.Int(required=True)


class BudgetCreateSchema(Schema):
    category_id = fields.Int(required=True)
    month = fields.Str(required=True, validate=validate.Regexp(r'^\d{4}-\d{2}$'))
    planned_amount = fields.Int(required=True, validate=validate.Range(min=1))


class BudgetUpdateSchema(Schema):
    planned_amount = fields.Int(required=True, validate=validate.Range(min=1))


class BudgetCopySchema(Schema):
    from_month = fields.Str(required=True, validate=validate.Regexp(r'^\d{4}-\d{2}$'))
    to_month = fields.Str(required=True, validate=validate.Regexp(r'^\d{4}-\d{2}$'))
