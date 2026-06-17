from unittest.mock import patch, Mock
import pytest
from app.services.monobank import MonobankConnector, MonobankRateLimitError, MonobankAPIError


def _mock_response(status_code, json_data=None, headers=None):
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.headers = headers or {}
    mock.ok = status_code < 400
    if status_code >= 400:
        mock.raise_for_status.side_effect = Exception(f'HTTP {status_code}')
    else:
        mock.raise_for_status = Mock()
    return mock


def test_get_client_info_success():
    payload = {
        'clientId': 'abc123',
        'name': 'Test User',
        'accounts': [{'id': 'acc1', 'currencyCode': 980, 'balance': 100000}],
    }
    with patch('requests.get', return_value=_mock_response(200, payload)):
        info = MonobankConnector('token').get_client_info()

    assert info['clientId'] == 'abc123'
    assert len(info['accounts']) == 1


def test_get_client_info_rate_limit():
    with patch('requests.get', return_value=_mock_response(429, headers={'Retry-After': '42'})):
        with pytest.raises(MonobankRateLimitError) as exc_info:
            MonobankConnector('token').get_client_info()

    assert exc_info.value.retry_after == 42


def test_get_client_info_http_error():
    with patch('requests.get', return_value=_mock_response(403)):
        with pytest.raises(Exception):
            MonobankConnector('token').get_client_info()


def test_get_statements_success():
    items = [
        {'id': 'tx1', 'time': 1700000000, 'amount': -5000, 'mcc': 5411,
         'description': 'ATB', 'currencyCode': 980},
    ]
    with patch('requests.get', return_value=_mock_response(200, items)):
        result = MonobankConnector('token').get_statements('acc1', 1699000000, 1700000000)

    assert len(result) == 1
    assert result[0]['id'] == 'tx1'


def test_get_statements_period_too_long():
    with pytest.raises(ValueError, match='31 days'):
        MonobankConnector('token').get_statements('acc1', 0, 9999999999)


def test_get_statements_rate_limit():
    with patch('requests.get', return_value=_mock_response(429, headers={'Retry-After': '60'})):
        with pytest.raises(MonobankRateLimitError) as exc_info:
            MonobankConnector('token').get_statements('acc1', 1699000000, 1700000000)

    assert exc_info.value.retry_after == 60


def test_setup_webhook_success():
    with patch('requests.post', return_value=_mock_response(200)):
        result = MonobankConnector('token').setup_webhook('https://example.com/hook')

    assert result is True


def test_setup_webhook_failure():
    with patch('requests.post', return_value=_mock_response(400)):
        result = MonobankConnector('token').setup_webhook('https://example.com/hook')

    assert result is False
