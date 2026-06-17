from unittest.mock import patch


# All analytics tests mock the service layer because analytics.py uses
# PostgreSQL-specific functions (func.to_char, func.extract) that don't
# work with the SQLite in-memory test database.

def test_spending_by_category_empty(auth_client):
    with patch('app.api.analytics.svc.spending_by_category', return_value=[]):
        res = auth_client.get('/api/analytics/spending-by-category')
    assert res.status_code == 200
    assert res.get_json() == []


def test_spending_by_category_with_data(auth_client):
    mock_data = [
        {'category_id': 1, 'category': {'id': 1, 'name': 'Food', 'icon': '🍔'},
         'amount': 50000, 'percentage': 100.0},
    ]
    with patch('app.api.analytics.svc.spending_by_category', return_value=mock_data):
        res = auth_client.get('/api/analytics/spending-by-category?from=2025-06-01&to=2025-06-30')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['amount'] == 50000


def test_spending_by_category_date_params(auth_client):
    with patch('app.api.analytics.svc.spending_by_category', return_value=[]) as mock_fn:
        auth_client.get('/api/analytics/spending-by-category?from=2025-01-01&to=2025-06-30')
    mock_fn.assert_called_once()


def test_monthly_trend(auth_client):
    mock_data = [
        {'month': '2025-05', 'income': 100000, 'expense': 40000},
        {'month': '2025-06', 'income': 120000, 'expense': 60000},
    ]
    with patch('app.api.analytics.svc.monthly_trend', return_value=mock_data):
        res = auth_client.get('/api/analytics/monthly-trend?months=2')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2
    assert data[1]['month'] == '2025-06'


def test_monthly_trend_clamps_to_max_24(auth_client):
    with patch('app.api.analytics.svc.monthly_trend', return_value=[]) as mock_fn:
        auth_client.get('/api/analytics/monthly-trend?months=100')
    called_months = mock_fn.call_args[0][1]
    assert called_months == 24


def test_monthly_trend_clamps_to_min_1(auth_client):
    with patch('app.api.analytics.svc.monthly_trend', return_value=[]) as mock_fn:
        auth_client.get('/api/analytics/monthly-trend?months=0')
    called_months = mock_fn.call_args[0][1]
    assert called_months == 1


def test_daily_heatmap(auth_client):
    mock_data = [
        {'day': 1, 'hour': 10, 'amount': 1500},
        {'day': 3, 'hour': 18, 'amount': 3000},
    ]
    with patch('app.api.analytics.svc.daily_heatmap', return_value=mock_data):
        res = auth_client.get('/api/analytics/daily-heatmap?month=2025-06')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2


def test_daily_heatmap_invalid_month_format(auth_client):
    res = auth_client.get('/api/analytics/daily-heatmap?month=2025/06')
    assert res.status_code == 422

    res = auth_client.get('/api/analytics/daily-heatmap?month=not-a-month')
    assert res.status_code == 422


def test_daily_heatmap_default_month(auth_client):
    with patch('app.api.analytics.svc.daily_heatmap', return_value=[]) as mock_fn:
        res = auth_client.get('/api/analytics/daily-heatmap')
    assert res.status_code == 200
    mock_fn.assert_called_once()


def test_summary_empty(auth_client):
    mock_data = {
        'total_income': 0,
        'total_expense': 0,
        'balance': 0,
        'top_categories': [],
    }
    with patch('app.api.analytics.svc.summary', return_value=mock_data):
        res = auth_client.get('/api/analytics/summary')
    assert res.status_code == 200
    data = res.get_json()
    assert data['total_income'] == 0
    assert data['top_categories'] == []


def test_summary_with_data(auth_client):
    mock_data = {
        'total_income': 200000,
        'total_expense': 80000,
        'balance': 120000,
        'top_categories': [
            {'category_id': 1, 'category': {'id': 1, 'name': 'Food', 'icon': '🍔'},
             'amount': 50000},
        ],
    }
    with patch('app.api.analytics.svc.summary', return_value=mock_data):
        res = auth_client.get('/api/analytics/summary')
    assert res.status_code == 200
    data = res.get_json()
    assert data['balance'] == 120000
    assert len(data['top_categories']) == 1


def test_summary_date_params(auth_client):
    mock_data = {'total_income': 0, 'total_expense': 0, 'balance': 0, 'top_categories': []}
    with patch('app.api.analytics.svc.summary', return_value=mock_data) as mock_fn:
        auth_client.get('/api/analytics/summary?from=2025-06-01&to=2025-06-30')
    mock_fn.assert_called_once()


def test_analytics_unauthenticated(client):
    endpoints = [
        '/api/analytics/spending-by-category',
        '/api/analytics/monthly-trend',
        '/api/analytics/daily-heatmap',
        '/api/analytics/summary',
    ]
    for url in endpoints:
        res = client.get(url)
        assert res.status_code == 401, f'Expected 401 for {url}'
