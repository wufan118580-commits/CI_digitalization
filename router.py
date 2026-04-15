"""API路由"""
import httpx
from fastapi import APIRouter, HTTPException, Request

from models import (
    LoginRequest, LoginResponse, CreateClassRequest,
    ClassInfo, ClassListResponse
)
from auth import jwt_required, get_current_org_id, get_current_openid, create_access_token
from database import execute_query, execute_write
from response import success_response, error_response
from config import WECHAT_APPID, WECHAT_SECRET

router = APIRouter(prefix="/api", tags=["机构管理"])


# ==================== 微信登录接口 ====================
@router.post("/login")
async def wechat_login(request: LoginRequest):
    """
    微信小程序登录接口
    接收微信授权code，返回JWT token
    """
    # 调用微信接口获取openid
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WECHAT_APPID,
        "secret": WECHAT_SECRET,
        "js_code": request.code,
        "grant_type": "authorization_code"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()
    except Exception as e:
        return error_response(code=500, msg=f"微信接口调用失败: {str(e)}")
    
    # 检查微信返回的错误
    if "errcode" in data and data["errcode"] != 0:
        return error_response(code=400, msg=data.get("errmsg", "微信授权失败"))
    
    openid = data.get("openid")
    if not openid:
        return error_response(code=400, msg="获取openid失败")
    
    # 查询或创建教师记录
    teacher = execute_query(
        "SELECT id, org_id FROM t_teacher WHERE openid = %s",
        (openid,),
        fetch_one=True
    )
    
    if not teacher:
        # 如果教师不存在，返回错误（需要先绑定机构）
        return error_response(code=404, msg="用户未注册，请先联系管理员")
    
    # 生成JWT token
    token = create_access_token(openid=openid, org_id=teacher["org_id"])
    
    return success_response(
        data=LoginResponse(
            token=token,
            openid=openid,
            org_id=teacher["org_id"]
        ).model_dump()
    )


# ==================== 班级管理接口 ====================
@router.post("/class")
@jwt_required
async def create_class(request: Request, class_req: CreateClassRequest):
    """
    创建班级接口
    POST /api/class
    自动从token中获取org_id
    """
    org_id = get_current_org_id(request)
    
    # 检查机构是否存在
    org = execute_query(
        "SELECT id FROM t_organization WHERE id = %s AND status = 1",
        (org_id,),
        fetch_one=True
    )
    if not org:
        return error_response(code=404, msg="机构不存在或已被禁用")
    
    # 插入班级记录
    sql = """
        INSERT INTO t_class (org_id, class_name, teacher_name)
        VALUES (%s, %s, %s)
    """
    class_id = execute_write(sql, (org_id, class_req.class_name, class_req.teacher_name or ""))
    
    return success_response(
        data={"id": class_id, "org_id": org_id, "class_name": class_req.class_name},
        msg="班级创建成功"
    )


@router.get("/class/list")
@jwt_required
async def get_class_list(request: Request):
    """
    查询班级列表
    GET /api/class/list
    只返回当前org_id的数据
    """
    org_id = get_current_org_id(request)
    
    # 查询班级列表
    sql = """
        SELECT id, org_id, class_name, teacher_name, created_at
        FROM t_class
        WHERE org_id = %s
        ORDER BY created_at DESC
    """
    classes = execute_query(sql, (org_id,))
    
    return success_response(
        data=ClassListResponse(
            total=len(classes),
            list=[ClassInfo(**c) for c in classes]
        ).model_dump()
    )


# ==================== 教师管理接口（示例）====================
@router.get("/teacher/info")
@jwt_required
async def get_teacher_info(request: Request):
    """获取当前教师信息"""
    openid = get_current_openid(request)
    org_id = get_current_org_id(request)
    
    sql = """
        SELECT id, openid, org_id, class_id, phone, role, created_at
        FROM t_teacher
        WHERE openid = %s AND org_id = %s
    """
    teacher = execute_query(sql, (openid, org_id), fetch_one=True)
    
    if not teacher:
        return error_response(code=404, msg="教师信息不存在")
    
    return success_response(data=teacher)
