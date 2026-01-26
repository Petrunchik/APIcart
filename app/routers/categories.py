from fastapi import APIRouter


router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.get("/")
async def get_all_categories():
    """
    Возвращает список всех категорий товаров
    """
    return {"message": "Список всех категорий"}


@router.post("/")
async def create_new_category():
    """
    Добавляет новую категорию
    """
    return {"message": "Категория создана"}


@router.put("/{category_id}")
async def update_category(category_id: int):
    """
    Изменяет категорию по ее ID
    """
    return {"message": "Категория обновлена"}


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """
    Удаляет категорию по ID
    """
    return {"message": "Категория удалена"}