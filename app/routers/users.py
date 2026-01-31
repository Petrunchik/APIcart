from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db
from app.schemas import UserCreate, UserAnswer
from app.models.users import User as UserModel
from app.auth import hash_password

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserAnswer, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Регистрирует нового пользователя
    """
    user_email = await db.scalar(select(UserModel).where(
        UserModel.email == user.email,
        UserModel.is_active == True
        ))
    if user_email is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The user with this email already exists")
    db_user = UserModel(
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user