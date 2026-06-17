import time
from datetime import datetime, timezone, timedelta

from ..extensions import db, celery
from ..models import Account, Transaction
from ..services.monobank import MonobankConnector, MonobankRateLimitError
from ..utils.encryption import decrypt_token

RATE_LIMIT_DELAY = 61   # safe margin over Monobank's 60s window
MAX_PERIOD = 2682000    # 31 days in seconds


def process_statement_item(account: Account, item: dict) -> Transaction | None:
    """
    Persist a single Monobank statement item.
    Returns the Transaction, or None if it was a duplicate.
    """
    if db.session.scalar(db.select(Transaction).filter_by(external_id=item['id'])):
        return None

    from ..services.categorizer import TransactionCategorizer
    category_id = TransactionCategorizer().categorize(
        mcc_code=item.get('mcc'),
        description=item.get('description', ''),
        user_id=account.user_id,
    )

    tx = Transaction(
        account_id=account.id,
        user_id=account.user_id,
        external_id=item['id'],
        amount=item['amount'],
        description=item.get('description', ''),
        mcc_code=item.get('mcc'),
        category_id=category_id,
        transaction_type='expense' if item['amount'] < 0 else 'income',
        currency_code=item.get('currencyCode', 980),
        timestamp=datetime.fromtimestamp(item['time'], tz=timezone.utc).replace(tzinfo=None),
        is_manual=False,
    )
    db.session.add(tx)
    return tx


@celery.task(bind=True, max_retries=5, default_retry_delay=65)
def import_account_transactions(self, account_id: int, months: int = 12):
    """
    Import the last N months of transactions for an account.
    Splits the range into 31-day chunks and waits 61s between requests
    to stay within Monobank's rate limit.
    """
    account = db.session.get(Account, account_id)
    if not account:
        return

    token = decrypt_token(account.encrypted_token)
    connector = MonobankConnector(token)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = int((datetime.now(timezone.utc) - timedelta(days=30 * months)).timestamp())

    chunks = []
    chunk_start = start_ts
    while chunk_start < now_ts:
        chunk_end = min(chunk_start + MAX_PERIOD, now_ts)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + 1

    for i, (from_ts, to_ts) in enumerate(chunks):
        try:
            items = connector.get_statements(account.bank_account_id, from_ts, to_ts)
        except MonobankRateLimitError as exc:
            raise self.retry(countdown=exc.retry_after)

        for item in items:
            process_statement_item(account, item)

        # Monobank returns items newest-first; the first item's balance
        # is the account balance after the most recent transaction.
        if i == len(chunks) - 1 and items:
            account.balance = items[0].get('balance', account.balance)

        db.session.commit()

        if i < len(chunks) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    account.last_sync_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
