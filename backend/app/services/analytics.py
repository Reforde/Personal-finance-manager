from datetime import datetime, timedelta

from sqlalchemy import case, func

from ..extensions import db
from ..models import Category, Transaction


def _months_ago(n: int) -> datetime:
    """Return the first day of the month N months before now."""
    now = datetime.utcnow()
    month = now.month - n
    year = now.year
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)


def spending_by_category(user_id: int, from_dt: datetime, to_dt: datetime) -> list:
    rows = db.session.execute(
        db.select(
            Transaction.category_id,
            func.sum(func.abs(Transaction.amount)).label('amount'),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'expense',
            Transaction.timestamp >= from_dt,
            Transaction.timestamp <= to_dt,
        )
        .group_by(Transaction.category_id)
    ).all()

    amounts = [int(r.amount) for r in rows]
    grand_total = sum(amounts)

    result = []
    for row, amount in zip(rows, amounts):
        category = db.session.get(Category, row.category_id) if row.category_id else None
        result.append({
            'category_id': row.category_id,
            'category': {
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
            } if category else None,
            'amount': amount,
            'percentage': round(amount / grand_total * 100, 2) if grand_total else 0.0,
        })

    return sorted(result, key=lambda x: x['amount'], reverse=True)


def monthly_trend(user_id: int, months: int = 12) -> list:
    start = _months_ago(months - 1)

    rows = db.session.execute(
        db.select(
            func.to_char(Transaction.timestamp, 'YYYY-MM').label('month'),
            func.sum(
                case(
                    (Transaction.transaction_type == 'income', Transaction.amount),
                    else_=0,
                )
            ).label('income'),
            func.sum(
                case(
                    (Transaction.transaction_type == 'expense', func.abs(Transaction.amount)),
                    else_=0,
                )
            ).label('expense'),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.timestamp >= start,
        )
        .group_by(func.to_char(Transaction.timestamp, 'YYYY-MM'))
        .order_by(func.to_char(Transaction.timestamp, 'YYYY-MM'))
    ).all()

    data_map = {
        r.month: {'income': int(r.income or 0), 'expense': int(r.expense or 0)}
        for r in rows
    }

    # Fill every month in the window with 0 so the chart never gets diagonal jumps
    result = []
    for i in range(months - 1, -1, -1):
        month_key = _months_ago(i).strftime('%Y-%m')
        result.append({'month': month_key, **data_map.get(month_key, {'income': 0, 'expense': 0})})
    return result


def daily_heatmap(user_id: int, month: str) -> list:
    start = datetime.strptime(month + '-01', '%Y-%m-%d')
    end = datetime(start.year + 1, 1, 1) if start.month == 12 \
        else datetime(start.year, start.month + 1, 1)

    rows = db.session.execute(
        db.select(
            func.extract('dow', Transaction.timestamp).label('day'),
            func.extract('hour', Transaction.timestamp).label('hour'),
            func.sum(func.abs(Transaction.amount)).label('amount'),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'expense',
            Transaction.timestamp >= start,
            Transaction.timestamp < end,
        )
        .group_by(
            func.extract('dow', Transaction.timestamp),
            func.extract('hour', Transaction.timestamp),
        )
        .order_by(
            func.extract('dow', Transaction.timestamp),
            func.extract('hour', Transaction.timestamp),
        )
    ).all()

    return [
        {'day': int(r.day), 'hour': int(r.hour), 'amount': r.amount}
        for r in rows
    ]


def summary(user_id: int, from_dt: datetime, to_dt: datetime) -> dict:
    base_filters = [
        Transaction.user_id == user_id,
        Transaction.timestamp >= from_dt,
        Transaction.timestamp <= to_dt,
    ]

    total_income = db.session.scalar(
        db.select(func.sum(Transaction.amount))
        .where(*base_filters, Transaction.transaction_type == 'income')
    ) or 0

    total_expense = abs(
        db.session.scalar(
            db.select(func.sum(Transaction.amount))
            .where(*base_filters, Transaction.transaction_type == 'expense')
        ) or 0
    )

    top_rows = db.session.execute(
        db.select(
            Transaction.category_id,
            func.sum(func.abs(Transaction.amount)).label('amount'),
        )
        .where(*base_filters, Transaction.transaction_type == 'expense',
               Transaction.category_id.isnot(None))
        .group_by(Transaction.category_id)
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
        .limit(5)
    ).all()

    top_categories = []
    for row in top_rows:
        category = db.session.get(Category, row.category_id)
        top_categories.append({
            'category_id': row.category_id,
            'category': {
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
            } if category else None,
            'amount': int(row.amount),
        })

    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'top_categories': top_categories,
    }
