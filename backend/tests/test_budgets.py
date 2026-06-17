import pytest
from app.models import Category


@pytest.fixture
def category(db):
    cat = Category(name='Food', user_id=None, is_default=False)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def budget(auth_client, category):
    res = auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 100000,
    })
    assert res.status_code == 201
    return res.get_json()


def test_list_budgets_empty(auth_client):
    res = auth_client.get('/api/budgets?month=2025-06')
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_budget(auth_client, category):
    res = auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 100000,
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['planned_amount'] == 100000
    assert data['month'] == '2025-06'
    assert data['spent'] == 0
    assert data['remaining'] == 100000
    assert data['progress'] == 0.0


def test_budget_includes_category_info(auth_client, category):
    res = auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 50000,
    })
    data = res.get_json()
    assert data['category']['name'] == 'Food'


def test_create_budget_duplicate(auth_client, category, budget):
    res = auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 50000,
    })
    assert res.status_code == 409


def test_create_budget_invalid_category(auth_client):
    res = auth_client.post('/api/budgets', json={
        'category_id': 99999,
        'month': '2025-06',
        'planned_amount': 100000,
    })
    assert res.status_code == 404


def test_create_budget_missing_fields(auth_client, category):
    res = auth_client.post('/api/budgets', json={'category_id': category.id})
    assert res.status_code == 422


def test_update_budget(auth_client, budget):
    budget_id = budget['id']
    res = auth_client.put(f'/api/budgets/{budget_id}', json={'planned_amount': 200000})
    assert res.status_code == 200
    assert res.get_json()['planned_amount'] == 200000


def test_update_budget_not_found(auth_client):
    res = auth_client.put('/api/budgets/99999', json={'planned_amount': 5000})
    assert res.status_code == 404


def test_delete_budget(auth_client, budget):
    budget_id = budget['id']
    res = auth_client.delete(f'/api/budgets/{budget_id}')
    assert res.status_code == 200

    res = auth_client.get('/api/budgets?month=2025-06')
    assert res.get_json() == []


def test_delete_budget_not_found(auth_client):
    res = auth_client.delete('/api/budgets/99999')
    assert res.status_code == 404


def test_copy_budgets(auth_client, category, budget):
    res = auth_client.post('/api/budgets/copy', json={
        'from_month': '2025-06',
        'to_month': '2025-07',
    })
    assert res.status_code == 201
    items = res.get_json()
    assert len(items) == 1
    assert items[0]['month'] == '2025-07'
    assert items[0]['planned_amount'] == 100000


def test_copy_budgets_same_month(auth_client, budget):
    res = auth_client.post('/api/budgets/copy', json={
        'from_month': '2025-06',
        'to_month': '2025-06',
    })
    assert res.status_code == 422


def test_copy_budgets_no_source(auth_client):
    res = auth_client.post('/api/budgets/copy', json={
        'from_month': '2020-01',
        'to_month': '2020-02',
    })
    assert res.status_code == 404


def test_copy_budgets_skips_existing(auth_client, category):
    auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 100000,
    })
    auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-07',
        'planned_amount': 999,
    })

    res = auth_client.post('/api/budgets/copy', json={
        'from_month': '2025-06',
        'to_month': '2025-07',
    })
    assert res.status_code == 201
    assert res.get_json() == []  # nothing new created, all already existed


def test_list_budgets_filtered_by_month(auth_client, category):
    auth_client.post('/api/budgets', json={
        'category_id': category.id,
        'month': '2025-06',
        'planned_amount': 100000,
    })
    cat2 = None
    res = auth_client.get('/api/budgets?month=2025-07')
    assert res.get_json() == []

    res = auth_client.get('/api/budgets?month=2025-06')
    assert len(res.get_json()) == 1


def test_unauthenticated_budgets(client):
    res = client.get('/api/budgets')
    assert res.status_code == 401
