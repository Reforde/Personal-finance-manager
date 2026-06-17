import re

from ..extensions import db
from ..models import Category, MCCMapping


class TransactionCategorizer:
    def categorize(self, mcc_code: int | None, description: str, user_id: int) -> int | None:
        """
        Priority order:
          1. User-specific MCC mapping
          2. User-specific description pattern
          3. System MCC mapping
          4. System description pattern
          5. Default fallback category
        """
        desc = description or ''

        # 1 & 2 — user rules
        if user_id:
            result = self._match_mcc(mcc_code, user_id=user_id)
            if result:
                return result
            result = self._match_description(desc, user_id=user_id)
            if result:
                return result

        # 3 & 4 — system rules
        result = self._match_mcc(mcc_code, user_id=None)
        if result:
            return result
        result = self._match_description(desc, user_id=None)
        if result:
            return result

        return self._default_category_id()

    def _match_mcc(self, mcc_code: int | None, user_id: int | None) -> int | None:
        if not mcc_code:
            return None

        mapping = db.session.scalar(
            db.select(MCCMapping)
            .join(Category, MCCMapping.category_id == Category.id)
            .where(
                MCCMapping.mcc_code == mcc_code,
                Category.user_id == user_id if user_id is None else Category.user_id == user_id,
            )
            .order_by(MCCMapping.priority.desc())
        )
        return mapping.category_id if mapping else None

    def _match_description(self, description: str, user_id: int | None) -> int | None:
        if not description:
            return None

        mappings = db.session.scalars(
            db.select(MCCMapping)
            .join(Category, MCCMapping.category_id == Category.id)
            .where(
                MCCMapping.description_pattern.isnot(None),
                Category.user_id.is_(None) if user_id is None else Category.user_id == user_id,
            )
            .order_by(MCCMapping.priority.desc())
        ).all()

        for mapping in mappings:
            try:
                if re.search(mapping.description_pattern, description, re.IGNORECASE):
                    return mapping.category_id
            except re.error:
                # Skip invalid regex patterns
                continue

        return None

    def _default_category_id(self) -> int | None:
        category = db.session.scalar(
            db.select(Category).filter_by(is_default=True, user_id=None)
        )
        return category.id if category else None
