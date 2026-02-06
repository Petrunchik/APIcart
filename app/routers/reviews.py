from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from app.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ReviewCreate, ReviewAnswer
from app.models import Product as ProductModel, User as UserModel
from app.models.reviews import Review as ReviewModel
from app.auth import get_current_buyer, get_current_admin_or_buyer


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

async def update_product_rating(product_id: int, db: AsyncSession):
    new_rating = await db.scalar(select(func.avg(ReviewModel.grade)).where(
        ReviewModel.product_id == product_id,
        ReviewModel.is_active == True
    ))
    product = await db.scalar(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.rating = new_rating
    await db.commit()


@router.get("/", response_model=list[ReviewAnswer], status_code=status.HTTP_200_OK)
async def get_all_review(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает все отзывы.
    """
    reviews_stmt = await db.scalars(select(ReviewModel).where(
        ReviewModel.is_active == True
    ))
    reviews = reviews_stmt.all()
    return reviews


@router.get("/products/{product_id}/reviews/", response_model=list[ReviewAnswer], status_code=status.HTTP_200_OK)
async def get_review_by_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
    ):
    """
    Получение отзывов о конкретном товаре по его ID.
    """
    product = await db.scalar(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    reviews_stmt = await db.scalars(select(ReviewModel).where(
        ReviewModel.product_id == product_id,
        ReviewModel.is_active == True
    ))
    reviews = reviews_stmt.all()
    return reviews


@router.post("/", response_model=ReviewAnswer, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: ReviewModel = Depends(get_current_buyer)):
    """
    Создание нового отзыва.
    """
    product = await db.scalar(select(ProductModel).where(
        ProductModel.id == review.product_id,
        ProductModel.is_active == True
    ))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await update_product_rating(product_id=review.product_id, db=db)
    await db.commit()
    return db_review


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_admin_or_buyer)
    ):
    """
    Удаление отзыва по ID.
    """
    review = await db.scalar(select(ReviewModel).where(
        ReviewModel.id == review_id,
        ReviewModel.is_active == True))
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own reviews."
        )
    review.is_active = False
    await update_product_rating(product_id=review.product_id, db=db)
    await db.commit()
    return {"message": "Review deleted"}