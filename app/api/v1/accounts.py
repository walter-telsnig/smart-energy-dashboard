# API = thin HTTP adapter. SRP: translate HTTP <-> use-cases/DTOs only.
# ADP: API depends inward on application layer; no infra details leak here.
# DIP: repo is injected at the edge.

from fastapi import APIRouter, Depends, HTTPException, status
from modules.accounts.dto import CreateUserDTO, UserReadDTO
from modules.accounts.use_cases import CreateUser, ListUsers, GetUser, UpdateUserName, DeleteUser
from infra.accounts.repository_sqlalchemy import SQLAlchemyUserRepository

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

def get_repo():
    return SQLAlchemyUserRepository()

@router.post("/", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserDTO, repo=Depends(get_repo)):
    return CreateUser(repo)(payload)

@router.get("/", response_model=list[UserReadDTO])
def list_users(limit: int = 100, offset: int = 0, repo=Depends(get_repo)):
    return list(ListUsers(repo)(limit=limit, offset=offset))

@router.get("/{user_id}", response_model=UserReadDTO)
def get_user(user_id: int, repo=Depends(get_repo)):
    out = GetUser(repo)(user_id)
    if not out:
        raise HTTPException(404, "User not found")
    return out

@router.patch("/{user_id}", response_model=UserReadDTO)
def update_user_name(user_id: int, full_name: str, repo=Depends(get_repo)):
    out = UpdateUserName(repo)(user_id, full_name)
    if not out:
        raise HTTPException(404, "User not found")
    return out

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, repo=Depends(get_repo)):
    if not DeleteUser(repo)(user_id):
        raise HTTPException(404, "User not found")
    return None
