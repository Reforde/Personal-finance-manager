import pytest
from app.models import Category, MCCMapping, User
from app.services.categorizer import TransactionCategorizer


@pytest.fixture
def default_cat(db):
    cat = Category(name='Інше', user_id=None, is_default=True)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def food_cat(db):
    cat = Category(name='Продукти', user_id=None, is_default=False)
    db.session.add(cat)
    db.session.flush()
    db.session.add(MCCMapping(mcc_code=5411, category_id=cat.id, priority=1))
    db.session.commit()
    return cat


def test_categorize_by_mcc(food_cat, default_cat):
    result = TransactionCategorizer().categorize(5411, 'ATB', user_id=None)
    assert result == food_cat.id


def test_unknown_mcc_falls_back_to_default(default_cat):
    result = TransactionCategorizer().categorize(9999, 'Unknown shop', user_id=None)
    assert result == default_cat.id


def test_no_mcc_falls_back_to_default(default_cat):
    result = TransactionCategorizer().categorize(None, 'Some description', user_id=None)
    assert result == default_cat.id


def test_description_pattern_match(db, default_cat):
    cat = Category(name='Аптека', user_id=None, is_default=False)
    db.session.add(cat)
    db.session.flush()
    db.session.add(MCCMapping(
        mcc_code=0,
        category_id=cat.id,
        description_pattern='аптека|pharmacy',
        priority=2,
    ))
    db.session.commit()

    result = TransactionCategorizer().categorize(None, 'АПТЕка Здоров`я', user_id=None)
    assert result == cat.id


def test_user_rule_overrides_system(db, default_cat):
    user = User(email='prio@test.com')
    user.set_password('pass12345')
    db.session.add(user)

    sys_cat = Category(name='System Food', user_id=None, is_default=False)
    db.session.add(sys_cat)
    db.session.flush()

    user_cat = Category(name='My Food', user_id=user.id, is_default=False)
    db.session.add(user_cat)
    db.session.flush()

    db.session.add(MCCMapping(mcc_code=5412, category_id=sys_cat.id, priority=1))
    db.session.add(MCCMapping(mcc_code=5412, category_id=user_cat.id, priority=1))
    db.session.commit()

    result = TransactionCategorizer().categorize(5412, '', user_id=user.id)
    assert result == user_cat.id


def test_invalid_regex_pattern_is_skipped(db, default_cat):
    cat = Category(name='Bad Pattern', user_id=None, is_default=False)
    db.session.add(cat)
    db.session.flush()
    db.session.add(MCCMapping(
        mcc_code=0,
        category_id=cat.id,
        description_pattern='[invalid(regex',
        priority=5,
    ))
    db.session.commit()

    # Should not raise, just skip the invalid pattern and fall back
    result = TransactionCategorizer().categorize(None, 'Test', user_id=None)
    assert result == default_cat.id


def test_higher_priority_wins(db, default_cat):
    cat_low = Category(name='Low Priority', user_id=None, is_default=False)
    cat_high = Category(name='High Priority', user_id=None, is_default=False)
    db.session.add_all([cat_low, cat_high])
    db.session.flush()

    db.session.add(MCCMapping(mcc_code=5499, category_id=cat_low.id, priority=1))
    db.session.add(MCCMapping(mcc_code=5499, category_id=cat_high.id, priority=10))
    db.session.commit()

    result = TransactionCategorizer().categorize(5499, '', user_id=None)
    assert result == cat_high.id
