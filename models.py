"""Pydantic模型定义"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求"""
    code: str = Field(..., description="微信授权code")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    openid: str
    org_id: int


class CreateClassRequest(BaseModel):
    """创建班级请求"""
    class_name: str = Field(..., min_length=1, max_length=100, description="班级名称")
    teacher_name: Optional[str] = Field(default="", max_length=50, description="班主任姓名")


class ClassInfo(BaseModel):
    """班级信息"""
    id: int
    org_id: int
    class_name: str
    teacher_name: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ClassListResponse(BaseModel):
    """班级列表响应"""
    total: int
    list: list[ClassInfo]
