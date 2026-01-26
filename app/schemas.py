from pydantic import BaseModel, Field, ConfigDict

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