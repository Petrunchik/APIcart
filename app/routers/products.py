from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update, func, desc, asc
from app.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ProductAnswer, ProductCreate, ProductList
from app.models import Product as ProductModel, Category as CategoryModel
from app.models.users import User as UserModel
from app.auth import get_current_seller

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=ProductList, status_code=status.HTTP_200_OK)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(
        None, description="ID категории для фильтрации."
    ),
    search: str | None = Query(
        None, min_length=1, description="Поиск по названию товара."
    ),
    min_price: float | None = Query(
        None, description="Минимальная цена для фильтрации."
    ),
    max_price: float | None = Query(
        None, description="Максимальная цена для фильтрации."
    ),
    in_stock: bool | None = Query(
        None, description="Наличие товаров для фильтрации. false - без остатка на складе."
    ),
    seller_id: int | None = Query(
        None, description="ID продавца для фильтрации."
    ),
    creation_date: bool | None = Query(
        None, description="Сортировка по дате создания, true - по возрастанию, false - по убыванию."
    ),
    update_date: bool | None = Query(
        None, description="Сортировка по дате обновления, true - по возрастанию, false - по убыванию."
    ),
    db: AsyncSession = Depends(get_async_db)
    ):
    """
    Получение списка всех товаров
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price не может быть больше max_price"
        )
    filters = [ProductModel.is_active == True]
    sorting_filters = []

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price > min_price)
    if max_price is not None:
        filters.append(ProductModel.price < max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)
    if creation_date is not None:
        sorting_filters.append(asc(ProductModel.created_at) if creation_date else desc(ProductModel.created_at))
    if update_date is not None:
        sorting_filters.append(asc(ProductModel.updated_at) if update_date else desc(ProductModel.updated_at))
    if sorting_filters == []:
        sorting_filters.append(ProductModel.id)
    
    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)
    
    rank_col = None

    if search:
        search_value = search.strip()
        if search_value:
            ts_query = func.websearch_to_tsquery('english', search_value)
            filters.append(ProductModel.tsv.op('@@')(ts_query))
            rank_col = func.ts_rank_cd(ProductModel.tsv, ts_query).label("rank")
            # total с учётом полнотекстового фильтра
            total_stmt = select(func.count()).select_from(ProductModel).where(*filters)

    total = await db.scalar(total_stmt) or 0
    
    if rank_col is not None:
        products_stmt = (
            select(ProductModel, rank_col)
            .where(*filters)
            .order_by(desc(rank_col), ProductModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(products_stmt)
        rows = result.all()
        items = [row[0] for row in rows]    # сами объекты
        # при желании можно вернуть ранг в ответе
        # ranks = [row.rank for row in rows]
    else:
        products_stmt = (
            select(ProductModel)
            .where(*filters)
            .order_by(ProductModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await db.scalars(products_stmt)).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


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