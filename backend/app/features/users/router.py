from fastapi import APIRouter, Depends

from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.features.users.schema import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
