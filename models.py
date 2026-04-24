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


# ==================== 机构相关 ====================

class CreateOrgRequest(BaseModel):
    """创建机构请求"""
    org_name: str = Field(..., min_length=1, max_length=100, description="机构名称")


class OrgInfo(BaseModel):
    """机构信息"""
    id: int
    org_name: str
    status: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class BindClassRequest(BaseModel):
    """绑定班级请求"""
    class_id: int = Field(..., description="班级ID")


# ==================== 班级相关 ====================

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


# ==================== 教师相关 ====================

class UpdateTeacherRequest(BaseModel):
    """更新教师信息请求"""
    phone: Optional[str] = Field(default="", max_length=20, description="手机号")
    class_id: Optional[int] = Field(default=None, description="绑定的班级ID")
