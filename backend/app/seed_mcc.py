import click
from flask.cli import with_appcontext
from .extensions import db
from .models import Category, MCCMapping

SYSTEM_CATEGORIES = [
    {'name': 'Продукти',    'icon': '🛒',  'mcc_codes': [5411, 5412, 5499]},
    {'name': 'Ресторани',   'icon': '🍽️',  'mcc_codes': [5812, 5811, 5814]},
    {'name': 'Паливо',      'icon': '⛽',  'mcc_codes': [5541, 5542, 5983]},
    {'name': 'Транспорт',   'icon': '🚌',  'mcc_codes': [4111, 4121, 4131, 7512]},
    {'name': 'Комунальні',  'icon': '🏠',  'mcc_codes': [4900, 4814]},
    {'name': 'Здоров\'я',   'icon': '🏥',  'mcc_codes': [5912, 8011, 8021, 8031, 8099]},
    {'name': 'Одяг',        'icon': '👕',  'mcc_codes': [5611, 5621, 5631, 5641, 5651, 5691]},
    {'name': 'Розваги',     'icon': '🎬',  'mcc_codes': [7832, 7841, 7911, 7922, 7991, 7999]},
    {'name': 'Переказ',     'icon': '💰',  'mcc_codes': [4829, 6010, 6011, 6012]},
    {'name': 'Зв\'язок',    'icon': '📱',  'mcc_codes': [4812, 4813, 4815]},
    {'name': 'Освіта',      'icon': '🎓',  'mcc_codes': [8211, 8220, 8241, 8244, 8249, 8299]},
    {'name': 'Інше',        'icon': '❓',  'mcc_codes': [], 'is_default': True},
]


@click.command('seed-mcc')
@with_appcontext
def seed_mcc_command():
    """Seed default categories and MCC mappings."""
    if Category.query.filter_by(user_id=None).first():
        click.echo('System categories already exist. Skipping.')
        return

    for cat_data in SYSTEM_CATEGORIES:
        category = Category(
            name=cat_data['name'],
            icon=cat_data['icon'],
            is_default=cat_data.get('is_default', False),
            user_id=None,
        )
        db.session.add(category)
        db.session.flush()

        for mcc_code in cat_data['mcc_codes']:
            db.session.add(MCCMapping(
                mcc_code=mcc_code,
                category_id=category.id,
                priority=1,
            ))

    db.session.commit()
    click.echo(f'Seeded {len(SYSTEM_CATEGORIES)} categories with MCC mappings.')
