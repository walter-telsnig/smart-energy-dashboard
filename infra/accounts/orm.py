# Infra ORM model. Implements persistence mapping only. SRP.
# ADP: Imports Base from infra.db; maps to domain entity via to_entity().

from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from infra.db import Base
from modules.accounts.domain import User

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    full_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(tz=timezone.utc))

    def to_entity(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            is_active=self.is_active,
            created_at=self.created_at,
        )
