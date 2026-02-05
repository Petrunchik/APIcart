from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.models.users import User as UserModel
from app.schemas import UserCreate, UserAnswer
from app.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_access_token

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


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)):
    """
    Аутентифицирует пользователя и возвращает JWT с email, role и id.
    """
    user_stmt = await db.scalars(select(UserModel).where(
        UserModel.email == form_data.username,
        UserModel.is_active == True
    ))
    user = user_stmt.first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return {"access_token": access_token, "token_type": "Bearer"}