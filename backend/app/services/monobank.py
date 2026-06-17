import requests


class MonobankAPIError(Exception):
    pass


class MonobankRateLimitError(MonobankAPIError):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f'Rate limit exceeded. Retry after {retry_after}s')


class MonobankConnector:
    BASE_URL = 'https://api.monobank.ua'
    MAX_PERIOD = 2682000  # 31 days in seconds

    def __init__(self, token: str):
        self.token = token
        self.headers = {'X-Token': token}

    def get_client_info(self) -> dict:
        response = requests.get(
            f'{self.BASE_URL}/personal/client-info',
            headers=self.headers,
            timeout=30,
        )
        if response.status_code == 429:
            raise MonobankRateLimitError(int(response.headers.get('Retry-After', 60)))
        response.raise_for_status()
        return response.json()

    def get_statements(self, account_id: str, from_ts: int, to_ts: int) -> list:
        if to_ts - from_ts > self.MAX_PERIOD:
            raise ValueError('Period exceeds 31 days. Split the request into smaller chunks.')

        url = f'{self.BASE_URL}/personal/statement/{account_id}/{from_ts}/{to_ts}'
        response = requests.get(url, headers=self.headers, timeout=30)

        if response.status_code == 429:
            raise MonobankRateLimitError(int(response.headers.get('Retry-After', 60)))
        response.raise_for_status()
        return response.json()

    def setup_webhook(self, webhook_url: str) -> bool:
        response = requests.post(
            f'{self.BASE_URL}/personal/webhook',
            headers=self.headers,
            json={'webHookUrl': webhook_url},
            timeout=30,
        )
        return response.ok
