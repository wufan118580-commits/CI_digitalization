import logging
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Institution,
    OrgUser,
    UserRole,
    InstitutionStatus,
)
from app.core.security import get_password_hash
from app.schemas.institution import InstitutionRegister

logger = logging.getLogger(__name__)


async def create_institution(db: AsyncSession, data: InstitutionRegister) -> Institution:
    """创建机构注册申请"""
    institution = Institution(
        name=data.name,
        contact_person=data.contact_person,
        contact_phone=data.contact_phone,
        address=data.address,
        status=InstitutionStatus.PENDING.value,
    )
    db.add(institution)
    await db.flush()
    await db.refresh(institution)
    logger.info(f"机构注册申请已提交: {institution.id} - {institution.name}")
    return institution


async def get_institution_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[int] = None,
    keyword: Optional[str] = None,
) -> tuple[list[Institution], int]:
    """
    获取机构列表（分页，支持状态和关键词筛选）
    返回: (数据列表, 总数)
    """
    query = select(Institution).where(Institution.is_delete == False)

    # 状态筛选
    if status_filter is not None:
        query = query.where(Institution.status == status_filter)

    # 关键词搜索（名称或手机号）
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.where(
            (Institution.name.like(like_pattern)) |
            (Institution.contact_phone.like(like_pattern))
        )

    # 总数查询
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页排序
    query = query.order_by(Institution.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    institutions = result.scalars().all()

    return list(institutions), total


async def get_institution_by_id(db: AsyncSession, institution_id: int) -> Optional[Institution]:
    """根据ID获取机构"""
    result = await db.execute(
        select(Institution).where(
            Institution.id == institution_id,
            Institution.is_delete == False,
        )
    )
    return result.scalar_one_or_none()


async def review_institution(
    db: AsyncSession,
    institution_id: int,
    new_status: int,
    remark: Optional[str] = None,
) -> dict:
    """
    审核机构
    - 通过时自动生成校长(principal)账号，默认密码为手机后4位
    - 拒绝时仅更新状态
    返回审核结果信息字典
    """
    institution = await get_institution_by_id(db, institution_id)
    if not institution:
        raise ValueError("机构不存在")

    if institution.status != InstitutionStatus.PENDING.value:
        raise ValueError(f"当前状态不允许操作，机构状态为: {institution.status}")

    # 更新机构状态
    institution.status = new_status
    await db.flush()

    result = {
        "institution_id": institution_id,
        "status": new_status,
        "principal_account": None,
        "default_password": None,
        "message": "",
    }

    # 审核通过 → 自动创建校长账号
    if new_status == InstitutionStatus.APPROVED.value:
        if not institution.contact_phone:
            raise ValueError("机构联系电话缺失，无法创建管理员账号")

        # 默认密码：手机后4位
        default_pwd = institution.contact_phone[-4:]
        password_hash = get_password_hash(default_pwd)

        # 检查是否已存在该校长的账号
        existing = await db.execute(
            select(OrgUser).where(
                OrgUser.institution_id == institution_id,
                OrgUser.role == UserRole.PRINCIPAL.value,
                OrgUser.is_delete == False,
            )
        )
        if existing.scalar_one_or_none():
            result["message"] = "审核通过（管理员账号已存在）"
            return result

        # 创建校长账号
        principal = OrgUser(
            institution_id=institution_id,
            name=institution.contact_person or institution.name,
            phone=institution.contact_phone,
            password_hash=password_hash,
            role=UserRole.PRINCIPAL.value,
        )
        db.add(principal)
        await db.flush()

        result["principal_account"] = institution.contact_phone
        result["default_password"] = f"{default_pwd[0]}***{default_pwd[-1]}"  # 部分遮掩
        result["message"] = "审核通过，管理员账号已创建"

    elif new_status == InstitutionStatus.REJECTED.value:
        result["message"] = "已拒绝该机构的注册申请"

    logger.info(f"机构审核完成: id={institution_id}, status={new_status}, remark={remark}")
    return result
