from pydantic import BaseModel, Field, ConfigDict, EmailStr
from decimal import Decimal
from datetime import datetime

class CategoryCreate(BaseModel):
    """
    Модель для содания и обновления категории. 

    POST и PUT запросы. 
    """
    name: str = Field(..., min_length=3, max_length=50, description="Название категории (3-50 символов)")
    parent_id: int | None = Field(None, description="ID родительской категории")


class CategoryAnswer(CategoryCreate):
    """
    Модель для ответа с данными категории. 

    GET запросы. 
    """
    id: int = Field(..., description="ID категории")
    is_active: bool = Field(..., description="Активность категории")

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара. 

    POST и PUT запросы. 
    """
    name: str = Field(..., min_length=3, max_length=100, description="Название категории (3-100 символов).")
    description: str | None = Field(None, max_length=500, description="Описание товара, не более 500 символов.")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Цена товара, больше 0.")
    image_url: str | None = Field(None, max_length=200, description="Ссылка на изображение товара.")
    stock: int = Field(..., ge=0, description="Остаток на складе, не меньше 0.")
    category_id: int = Field(..., description="ID категориии, к которой относится товар.")


class ProductAnswer(ProductCreate):
    """
    Модель для ответа с данными товара.

    GET запросы.
    """
    id: int = Field(..., description="ID товара.")
    is_active: bool = Field(..., description="Активность товара.")
    rating: Decimal = Field(default=0.0, description="Рейтинг товара")
    created_at: datetime = Field(default=datetime.now(), description="Время создания записи.")
    updated_at: datetime = Field(default=datetime.now(), description="Время обновления записи.")

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """
    Список пагинации для товаров.
    """
    items: list[ProductAnswer] = Field(description="Список товаров")
    total: int = Field(ge=0, description="Общее количество товаров")
    page: int = Field(ge=1, description="Номер текущей страницы")
    page_size: int = Field(ge=1, description="Количество элементов на странице")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    Модель для создания и обновления пользователя.
    """
    email: EmailStr = Field(..., description="Email пользователя.")
    password: str = Field(..., min_length=10, description="Пароль (не менее 10 символов)")
    role: str = Field(
        default="buyer",
        pattern="^(buyer|seller|admin)$",
        description="Роль пользователя: buyer, seller или admin"
    )


class UserAnswer(BaseModel):
    """
    Модель для ответа с данными пользователя.
    """
    id: int
    email: EmailStr
    role: str 
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    """
    Модель для создания и обновления отзыва. 
    """
    grade: int = Field(..., ge=1, le=5, description="Оценка товара")
    product_id: int = Field(..., description="ID товара, которому принадлежит отзыв")
    comment: str | None = Field(None, max_length=1000, description="Комментарий")


class ReviewAnswer(ReviewCreate):
    """
    Модель для ответов с данными отзыва.
    """
    comment_date: datetime = Field(default=datetime.now(), description="Время создания отзыва")
    id: int = Field(..., description="ID отзыва")
    user_id: int = Field(..., description="ID пользователя, которому принадлежит отзыв")
    is_active: bool = Field(default=True, description="Активность отзыва")

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """
    Модель для ответа refresh-токена
    """
    refresh_token: str