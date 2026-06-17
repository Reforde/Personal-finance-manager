from datetime import datetime

from sqlalchemy import func

from ..extensions import db
from ..models import Budget, Notification, Transaction


def check_budget(tx: Transaction) -> None:
    """Create budget_warning / budget_exceeded notification if thresholds crossed.

    Called both from the Monobank webhook and from manual transaction creation
    so that notifications work regardless of how the transaction was added.
    """
    if not tx.category_id or tx.transaction_type != 'expense':
        return

    month = tx.timestamp.strftime('%Y-%m')
    budget = db.session.scalar(
        db.select(Budget).filter_by(
            user_id=tx.user_id,
            category_id=tx.category_id,
            month=month,
        )
    )
    if not budget or budget.planned_amount == 0:
        return

    month_start = datetime.strptime(month + '-01', '%Y-%m-%d')
    if month_start.month == 12:
        month_end = datetime(month_start.year + 1, 1, 1)
    else:
        month_end = datetime(month_start.year, month_start.month + 1, 1)

    spent_abs = abs(
        db.session.scalar(
            db.select(func.sum(Transaction.amount)).where(
                Transaction.user_id == tx.user_id,
                Transaction.category_id == tx.category_id,
                Transaction.transaction_type == 'expense',
                Transaction.timestamp >= month_start,
                Transaction.timestamp < month_end,
            )
        ) or 0
    )

    ratio = spent_abs / budget.planned_amount

    if ratio >= 1.0:
        notif_type = 'budget_exceeded'
        message = (
            f'Бюджет "{budget.category.name}" перевищено: '
            f'витрачено {spent_abs / 100:.2f} грн '
            f'з {budget.planned_amount / 100:.2f} грн ({month})'
        )
    elif ratio >= 0.7:
        notif_type = 'budget_warning'
        message = (
            f'Бюджет "{budget.category.name}" майже вичерпано: '
            f'{ratio * 100:.0f}% використано ({month})'
        )
    else:
        return

    already_notified = db.session.scalar(
        db.select(Notification).where(
            Notification.user_id == tx.user_id,
            Notification.type == notif_type,
            Notification.message.contains(month),
            Notification.message.contains(budget.category.name),
        )
    )
    if not already_notified:
        db.session.add(Notification(
            user_id=tx.user_id,
            type=notif_type,
            message=message,
        ))
