# Domain entity = business meaning + invariants. No DB/HTTP dependencies. SRP.

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class User:
    id: Optional[int]
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
