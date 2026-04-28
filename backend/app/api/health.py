from fastapi import APIRouter
from app.core.response import success_response

router = APIRouter(prefix="/api", tags=["系统"])


@router.get("/health")
async def health_check():
    """
    健康检查接口
    检测服务状态、数据库连接等
    """
    # TODO: 可在此处添加数据库连接检测等逻辑
    return success_response({
        "status": "ok",
        "service": "家校互通平台",
        "version": "1.0.0",
    })
