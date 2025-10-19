# Infra adapter implements the Port. DIP: app depends on the port; we adapt here.

from typing import Iterable, Optional
from sqlalchemy import select
from infra.db import SessionLocal
from modules.accounts.dto import CreateUserDTO
from modules.accounts.domain import User
from modules.accounts.ports import UserRepositoryPort
from .orm import UserORM

class SQLAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session_factory=SessionLocal):
        self._sf = session_factory  # session factory injected (testable)

    def create(self, dto: CreateUserDTO) -> User:
        with self._sf() as s:
            orm = UserORM(email=dto.email, full_name=dto.full_name, is_active=True)
            s.add(orm)
            s.commit()
            s.refresh(orm)
            return orm.to_entity()

    def get(self, user_id: int) -> Optional[User]:
        with self._sf() as s:
            orm = s.get(UserORM, user_id)
            return orm.to_entity() if orm else None

    def list(self, limit: int = 100, offset: int = 0) -> Iterable[User]:
        with self._sf() as s:
            rows = s.execute(
                select(UserORM).order_by(UserORM.id).limit(limit).offset(offset)
            ).scalars().all()
            return [r.to_entity() for r in rows]

    def update_name(self, user_id: int, full_name: str) -> Optional[User]:
        with self._sf() as s:
            orm = s.get(UserORM, user_id)
            if not orm:
                return None
            orm.full_name = full_name
            s.commit()
            s.refresh(orm)
            return orm.to_entity()

    def delete(self, user_id: int) -> bool:
        with self._sf() as s:
            orm = s.get(UserORM, user_id)
            if not orm:
                return False
            s.delete(orm)
            s.commit()
            return True
