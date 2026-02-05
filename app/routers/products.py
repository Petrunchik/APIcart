from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from app.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ProductAnswer, ProductCreate
from app.models import Product as ProductModel, Category as CategoryModel
from app.models.users import User as UserModel
from app.auth import get_current_seller

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=list[ProductAnswer], status_code=status.HTTP_200_OK)
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Получение списка всех товаров
    """
    stmt = await db.scalars(select(ProductModel).where(
        ProductModel.is_active == True
    ))
    products = stmt.all()
    return products


@router.get("/{product_id}", response_model=list[ProductAnswer], status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получение товара по ID
    """
    stmt = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = stmt.all()
    return db_product
    


@router.get("/category/{category_id}", response_model=list[ProductAnswer], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получение товаров категории по ID
    """
    category_stmt = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
    ))
    db_category = category_stmt.first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found!")
    product_stmt = await db.scalars(select(ProductModel).where(
        ProductModel.category_id == category_id,
        ProductModel.is_active == True
    ))
    db_products = product_stmt.all()
    return db_products


@router.post("/", response_model=ProductAnswer, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)):
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    stmt = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == product.category_id,
        CategoryModel.is_active == True
    ))
    db_category = stmt.first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found!")
    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductAnswer, status_code=status.HTTP_200_OK)
async def update_product(
    product_id: int,
    updated_product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)):
    """
    Изменение товара по ID, только если он принадлежит текущему продавцу.
    """
    product_stmt = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = product_stmt.first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can update only your own products")
    category_stmt = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == db_product.category_id,
        CategoryModel.is_active == True
    ))
    db_category = category_stmt.first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
    await db.execute(update(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ).values(**updated_product.model_dump()))
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)):
    """
    Удаление товара по ID, только если он принадлежит текущему продавцу.
    """
    stmt = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = stmt.first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    db_product.is_active = False
    await db.commit()
    await db.refresh(db_product)
    return {"message": "Product is marked as deleted"}