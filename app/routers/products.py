from fastapi import APIRouter

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/")
async def get_all_products():
    """
    Получение списка всех товаров
    """
    return {"message": "Список всех товаров"}


@router.get("/{product_id}")
async def get_product(product_id: int):
    """
    Получение товара по ID
    """
    return {"message": f"Товар с ID: {product_id}"}


@router.get("/category/{category_id}")
async def get_products_by_category(category_id: int):
    """
    Получение товаров категории по ID
    """
    return {"message": f"Список всех товаров категории {category_id}"}


@router.post("/")
async def create_product():
    """
    Добавление нового товара
    """
    return {"message": "Создание нового товаров"}


@router.put("/{product_id}")
async def update_product():
    """
    Изменение товара по ID
    """
    return {"message": "Товар изменен"}


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """
    Удаление товара по ID
    """
    return {"message": f"Товар с ID: {product_id} удален"}