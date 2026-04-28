import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles, Role
from app.core.response import success_response, error_response, paginate_response
from app.services.institution import (
    create_institution,
    get_institution_list,
    get_institution_by_id,
    review_institution,
)
from app.schemas.institution import (
    InstitutionRegister,
    InstitutionReview,
    InstitutionResponse,
    InstitutionReviewResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/platform", tags=["机构管理"])


@router.post("/institutions/", summary="提交机构注册申请")
async def register_institution(
    body: InstitutionRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    提交机构注册申请（无需认证）

    - **name**: 机构名称 (必填, 2-100字符)
    - **contact_person**: 联系人 (必填)
    - **contact_phone**: 联系电话 (必填, 11位手机号)
    - **address**: 地址 (选填)
    """
    try:
        institution = await create_institution(db, body)
        return success_response(
            data={"id": institution.id, "name": institution.name},
            msg="注册申请已提交，请等待审核",
        )
    except Exception as e:
        logger.error(f"机构注册失败: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"注册失败: {str(e)}")


@router.get(
    "/institutions/",
    response_model=None,
    summary="获取机构列表（平台管理员）",
)
async def list_institutions(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    status: int | None = Query(default=None, ge=0, le=2, description="状态筛选"),
    keyword: str | None = Query(default=None, description="关键词搜索"),
    _current_user: dict = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    平台管理员查看机构列表（需管理员token）

    支持:
    - 分页 (page, page_size)
    - 状态筛选 (0待审核 1已通过 2已拒绝)
    - 关键词搜索 (机构名称/手机号)
    """
    institutions, total = await get_institution_list(
        db,
        page=page,
        page_size=page_size,
        status_filter=status,
        keyword=keyword,
    )

    items = [
        InstitutionResponse.model_validate(inst).model_dump()
        for inst in institutions
    ]

    return paginate_response(items, total, page, page_size)


@router.put(
    "/institutions/{institution_id}/review",
    summary="审批机构（平台管理员）",
)
async def review_institution_api(
    institution_id: int = Path(..., description="机构ID"),
    body: InstitutionReview = ...,
    _current_user: dict = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    平台管理员审批机构（需管理员token）

    - **status**: 审核结果 (1=通过, 2=拒绝)
    - **remark**: 审核备注 (选填)

    **通过后行为**:
    - 自动创建角色为 principal 的管理员账号
    - 登录账号 = 机构联系电话
    - 默认密码 = 手机号后4位（建议用户首次登录后修改）
    """
    try:
        result = await review_institution(
            db=db,
            institution_id=institution_id,
            new_status=body.status,
            remark=body.remark,
        )
        return success_response(
            data=InstitutionReviewResponse(**result).model_dump(),
            msg=result.get("message", "审核完成"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"机构审核失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"审核处理失败: {str(e)}")
