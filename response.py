"""统一响应格式"""
from typing import Any, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = 200
    data: Any = None
    msg: str = ""


def success_response(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return ResponseModel(code=200, data=data, msg=msg).model_dump()


def error_response(code: int = 400, data: Any = None, msg: str = "error") -> dict:
    """错误响应"""
    return ResponseModel(code=code, data=data, msg=msg).model_dump()
