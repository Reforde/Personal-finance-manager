import pytest
from app.models import Category


@pytest.fixture
def system_default(db):
    cat = Category(name='Інше', user_id=None, is_default=True)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def user_cat(auth_client):
    res = auth_client.post('/api/categories', json={'name': 'Продукти', 'icon': '🛒'})
    assert res.status_code == 201
    return res.get_json()


def test_list_categories_empty(auth_client):
    res = auth_client.get('/api/categories')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_list_includes_system_categories(auth_client, db):
    sys_cat = Category(name='System', user_id=None, is_default=False)
    db.session.add(sys_cat)
    db.session.commit()

    res = auth_client.get('/api/categories')
    names = [c['name'] for c in res.get_json()]
    assert 'System' in names


def test_create_category(auth_client):
    res = auth_client.post('/api/categories', json={'name': 'Food', 'icon': '🍔'})
    assert res.status_code == 201
    data = res.get_json()
    assert data['name'] == 'Food'
    assert data['icon'] == '🍔'
    assert data['is_default'] is False


def test_create_category_no_icon(auth_client):
    res = auth_client.post('/api/categories', json={'name': 'NoIcon'})
    assert res.status_code == 201
    assert res.get_json()['name'] == 'NoIcon'


def test_create_category_missing_name(auth_client):
    res = auth_client.post('/api/categories', json={'icon': '🍔'})
    assert res.status_code == 422


def test_create_category_with_valid_parent(auth_client, db):
    sys_parent = Category(name='Parent', user_id=None, is_default=False)
    db.session.add(sys_parent)
    db.session.commit()

    res = auth_client.post('/api/categories', json={
        'name': 'Child',
        'parent_id': sys_parent.id,
    })
    assert res.status_code == 201
    assert res.get_json()['parent_id'] == sys_parent.id


def test_create_category_invalid_parent(auth_client):
    res = auth_client.post('/api/categories', json={
        'name': 'Child',
        'parent_id': 99999,
    })
    assert res.status_code == 404


def test_update_category(auth_client, user_cat):
    cat_id = user_cat['id']
    res = auth_client.put(f'/api/categories/{cat_id}', json={'name': 'Updated', 'icon': '✏️'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['name'] == 'Updated'
    assert data['icon'] == '✏️'


def test_update_category_partial(auth_client, user_cat):
    cat_id = user_cat['id']
    res = auth_client.put(f'/api/categories/{cat_id}', json={'name': 'OnlyName'})
    assert res.status_code == 200
    assert res.get_json()['name'] == 'OnlyName'


def test_cannot_update_system_category(auth_client, db):
    sys_cat = Category(name='System', user_id=None, is_default=False)
    db.session.add(sys_cat)
    db.session.commit()

    res = auth_client.put(f'/api/categories/{sys_cat.id}', json={'name': 'Hacked'})
    assert res.status_code == 404


def test_delete_category(auth_client, db, user_cat, system_default):
    cat_id = user_cat['id']
    res = auth_client.delete(f'/api/categories/{cat_id}')
    assert res.status_code == 200

    res = auth_client.get('/api/categories')
    ids = [c['id'] for c in res.get_json()]
    assert cat_id not in ids


def test_cannot_delete_system_category(auth_client, db):
    sys_cat = Category(name='System', user_id=None, is_default=False)
    db.session.add(sys_cat)
    db.session.commit()

    res = auth_client.delete(f'/api/categories/{sys_cat.id}')
    assert res.status_code == 404


def test_unauthenticated_access(client):
    res = client.get('/api/categories')
    assert res.status_code == 401

    res = client.post('/api/categories', json={'name': 'x'})
    assert res.status_code == 401
