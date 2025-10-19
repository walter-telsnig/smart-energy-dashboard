# Application layer: orchestration of domain + ports. SRP (one job each). DIP.

from typing import Iterable
from .ports import UserRepositoryPort
from .dto import CreateUserDTO, UserReadDTO

class CreateUser:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def __call__(self, dto: CreateUserDTO) -> UserReadDTO:
        # Convert entity -> DTO at boundary
        return UserReadDTO.model_validate(self.repo.create(dto))

class ListUsers:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def __call__(self, limit: int = 100, offset: int = 0) -> Iterable[UserReadDTO]:
        return [UserReadDTO.model_validate(u) for u in self.repo.list(limit, offset)]

class GetUser:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def __call__(self, user_id: int) -> UserReadDTO | None:
        u = self.repo.get(user_id)
        return UserReadDTO.model_validate(u) if u else None

class UpdateUserName:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def __call__(self, user_id: int, full_name: str) -> UserReadDTO | None:
        u = self.repo.update_name(user_id, full_name)
        return UserReadDTO.model_validate(u) if u else None

class DeleteUser:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def __call__(self, user_id: int) -> bool:
        return self.repo.delete(user_id)
