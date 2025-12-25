"""
Accounts API router (FastAPI)

Exposes CRUD endpoints under /api/v1/accounts:
- POST   /        -> create account (201)
- GET    /        -> list accounts (200)
- GET    /{id}    -> get account by id (200 or 404)
- PATCH  /{id}    -> partial update via JSON body or query params (200, 404, 409, 422)
- DELETE /{id}    -> delete account (204 or 404)

Design (lecture slides principles):
- SRP: HTTP + validation only; persistence via SQLAlchemy model in modules/accounts/model.py
- DIP/ADP: DB session injected via infra.db.get_db; no engine creation in this layer
- Versioning: '/api/v1' applied in app.main include_router; local prefix is '/accounts'
- Pydantic v2 models (from_attributes=True); Email uniqueness guarded
"""


from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from infra.db import get_db
from modules.accounts.model import Account
from core.security import get_password_hash

router = APIRouter(prefix="/accounts", tags=["accounts"])

class AccountCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class AccountUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None

class AccountRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    model_config = ConfigDict(from_attributes=True)

def _get_account_or_404(db: Session, user_id: int) -> Account:
    obj = db.get(Account, user_id)
    if not obj:
        raise HTTPException(status_code=404, detail="account not found")
    return obj

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    exists = db.query(Account).filter(Account.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="email already exists")
    
    hashed_pw = get_password_hash(payload.password)
    obj = Account(
        email=payload.email, 
        full_name=payload.full_name,
        hashed_password=hashed_pw
    )
    db.add(obj)
    db.commit() 
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id).all()

@router.get("/{user_id}", response_model=AccountRead)
def get_account(user_id: int, db: Session = Depends(get_db)):
    return _get_account_or_404(db, user_id)

@router.patch("/{user_id}", response_model=AccountRead)
def update_account(
    user_id: int,
    payload: AccountUpdate | None = Body(default=None),
    email: EmailStr | None = Query(default=None),
    full_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    obj = _get_account_or_404(db, user_id)
    effective = payload or AccountUpdate(email=email, full_name=full_name)

    if effective.email is None and effective.full_name is None:
        raise HTTPException(status_code=422, detail="no fields provided to update")

    if effective.email is not None:
        exists = db.query(Account).filter(Account.email == effective.email, Account.id != user_id).first()
        if exists:
            raise HTTPException(status_code=409, detail="email already exists")
        obj.email = effective.email
    
    if effective.full_name is not None:
        obj.full_name = effective.full_name

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user_id: int, db: Session = Depends(get_db)):
    obj = _get_account_or_404(db, user_id)
    db.delete(obj)
    db.commit()
    return None
