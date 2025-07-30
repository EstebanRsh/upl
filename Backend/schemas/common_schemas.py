# schemas/common_schemas.py
from pydantic import BaseModel
from typing import List, TypeVar, Generic

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total_items: int
    total_pages: int
    current_page: int
    items: List[T]
