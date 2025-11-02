from datetime import datetime, timezone
from modules.accounts.dto import CreateUserDTO
from modules.accounts.use_cases import CreateUser, ListUsers
from modules.accounts.ports import UserRepositoryPort
from modules.accounts.domain import User

class FakeRepo(UserRepositoryPort):
    def __init__(self):
        self._d = {}
        self._seq = 0
    def create(self, dto: CreateUserDTO) -> User:
        self._seq += 1
        u = User(self._seq, dto.email, dto.full_name, True, datetime.now(tz=timezone.utc))
        self._d[self._seq] = u
        return u
    def get(self, user_id: int): return self._d.get(user_id)
    def list(self, limit=100, offset=0): return list(self._d.values())[offset:offset+limit]
    def update_name(self, user_id: int, full_name: str):
        u = self._d.get(user_id)
        if not u:
            return None
        u = User(u.id, u.email, full_name, u.is_active, u.created_at)
        self._d[user_id] = u
        return u
    def delete(self, user_id: int) -> bool: return self._d.pop(user_id, None) is not None

def test_create_and_list():
    repo = FakeRepo()
    out = CreateUser(repo)(CreateUserDTO(email="a@e.com", full_name="Alice"))
    assert out.email == "a@e.com"
    assert len(list(ListUsers(repo)())) == 1
