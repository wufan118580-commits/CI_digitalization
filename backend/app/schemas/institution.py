from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 机构注册相关 Schema
# ============================================================
class InstitutionRegister(BaseModel):
    """机构注册请求"""
    name: str = Field(..., min_length=2, max_length=100, description="机构名称")
    contact_person: str = Field(..., min_length=1, max_length=50, description="联系人")
    contact_phone: str = Field(
        ..., pattern=r"^1[3-9]\d{9}$", description="联系电话(11位手机号)"
    )
    address: Optional[str] = Field(None, max_length=255, description="地址")


class InstitutionListQuery(BaseModel):
    """机构列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: Optional[int] = Field(default=None, ge=0, le=2, description="状态筛选")
    keyword: Optional[str] = Field(default=None, max_length=100, description="关键词搜索(名称/手机号)")


class InstitutionReview(BaseModel):
    """机构审核请求"""
    status: int = Field(..., ge=1, le=2, description="审核状态: 1通过 2拒绝")
    remark: Optional[str] = Field(default=None, max_length=500, description="审核备注")


# ============================================================
# 响应 Schema
# ============================================================
class InstitutionResponse(BaseModel):
    """机构信息响应"""
    id: int
    name: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: int
    face_enabled: bool = False
    face_expire_date: Optional[date] = None
    created_at: str = ""

    model_config = {"from_attributes": True}


class InstitutionDetailResponse(InstitutionResponse):
    """机构详情响应（含管理员账号信息）"""
    principal_name: Optional[str] = None
    principal_phone: Optional[str] = None


class InstitutionReviewResponse(BaseModel):
    """审核结果响应"""
    institution_id: int
    status: int
    principal_account: Optional[str] = None   # 审核通过时返回生成的管理员账号
    default_password: Optional[str] = None     # 审核通过时返回默认密码提示
    message: str = ""
