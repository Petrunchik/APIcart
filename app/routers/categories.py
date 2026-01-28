from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.db_depends import get_db
from app.schemas import CategoryAnswer, CategoryCreate
from app.models.categories import Category as CategoryModel

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.get("/", response_model=list[CategoryAnswer], status_code=status.HTTP_200_OK)
async def get_all_categories(db: Session = Depends(get_db)):
    """
    Возвращает список всех категорий товаров
    """
    categories = db.scalars(select(CategoryModel).where(CategoryModel.is_active == True)).all()
    return categories


@router.post("/", response_model=CategoryAnswer, status_code=status.HTTP_201_CREATED)
async def create_new_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
    Добавляет новую категорию
    """
    if category.parent_id is not None:
        parent = db.scalars(
            select(CategoryModel).where(
                CategoryModel.id == category.parent_id,
                CategoryModel.is_active == True)
                ).first()
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found!")
        
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategoryAnswer, status_code=status.HTTP_200_OK)
async def update_category(category_id: int, updated_category: CategoryCreate, db: Session = Depends(get_db)):
    """
    Изменяет категорию по ее ID
    """
    category = db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
        )).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found!")
    if category.parent_id is not None:
        parent = db.scalars(select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active == True
        )).first()
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")
    
    db.execute(update(CategoryModel).where(
        CategoryModel.id == category_id
    ).values(**updated_category.model_dump()))
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Удаляет категорию по ID
    """
    category = db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
    )).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found!")
    category.is_active = False
    db.commit()
    return {"message": "Category is marked as deleted"}