from datetime import datetime
from sqlalchemy import Boolean, Integer, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment: Mapped[str | None] = mapped_column(Text)
    comment_date: Mapped[Date] = mapped_column(Date, default=datetime.now(), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    user_review: Mapped["User"] = relationship(
        "User",
        back_populates=""
    )
    product_review: Mapped["Product"] = relationship(
        "Product",
        back_populates="reviews"
    )