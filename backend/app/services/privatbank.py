import json
import requests
import redis as redis_lib


class PrivatBankAPIError(Exception):
    pass


class PrivatBankConnector:
    CURRENT_URL = 'https://api.privatbank.ua/p24api/pubinfo'
    ARCHIVE_URL = 'https://api.privatbank.ua/p24api/exchange_rates'
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, redis_client: redis_lib.Redis = None):
        self._redis = redis_client

    def get_current_rates(self) -> list:
        cache_key = 'rates:current'

        if self._redis:
            cached = self._redis.get(cache_key)
            if cached:
                return json.loads(cached)

        try:
            response = requests.get(
                self.CURRENT_URL,
                params={'exchange': '', 'coursid': 5},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise PrivatBankAPIError(str(e)) from e

        rates = response.json()

        if self._redis:
            self._redis.setex(cache_key, self.CACHE_TTL, json.dumps(rates))

        return rates

    def get_archive_rates(self, date: str) -> list:
        """
        date: "DD.MM.YYYY" — e.g. "01.06.2025"
        Returns a list of exchange rate objects from PrivatBank.
        """
        cache_key = f'rates:archive:{date}'

        if self._redis:
            cached = self._redis.get(cache_key)
            if cached:
                return json.loads(cached)

        try:
            response = requests.get(
                self.ARCHIVE_URL,
                params={'date': date},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise PrivatBankAPIError(str(e)) from e

        rates = response.json().get('exchangeRate', [])

        if self._redis:
            self._redis.setex(cache_key, self.CACHE_TTL, json.dumps(rates))

        return rates


def get_redis_client(redis_url: str) -> redis_lib.Redis:
    return redis_lib.from_url(redis_url, decode_responses=True)
