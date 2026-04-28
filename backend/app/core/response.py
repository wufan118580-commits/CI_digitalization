from datetime import datetime
from typing import Any, Generic, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None
    timestamp: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def success_response(data: Any = None, msg: str = "success") -> dict[str, Any]:
    """构建成功响应"""
    return ResponseModel(code=0, msg=msg, data=data).model_dump()


def error_response(msg: str, code: int = -1, data: Any = None) -> dict[str, Any]:
    """构建错误响应"""
    return ResponseModel(code=code, msg=msg, data=data).model_dump()


def paginate_response(items: list, total: int, page: int, page_size: int) -> dict[str, Any]:
    """构建分页响应"""
    data = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }
    return success_response(data)
