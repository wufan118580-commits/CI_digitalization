"""API路由"""
import httpx
from fastapi import APIRouter, Request

from models import (
    LoginRequest, LoginResponse,
    CreateOrgRequest, OrgInfo,
    CreateClassRequest, ClassInfo, ClassListResponse,
    BindClassRequest, UpdateTeacherRequest,
)
from auth import jwt_required, get_current_org_id, get_current_openid, create_access_token
from database import execute_query, execute_write
from response import success_response, error_response
from config import WECHAT_APPID, WECHAT_SECRET

router = APIRouter(prefix="/api", tags=["机构管理"])


# ==================== 微信登录接口 ====================
@router.post("/login")
async def wechat_login(request: LoginRequest):
    """微信小程序登录接口 - 接收code，返回JWT token（支持自动注册）"""
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
    
    if "errcode" in data and data["errcode"] != 0:
        return error_response(code=400, msg=data.get("errmsg", "微信授权失败"))
    
    openid = data.get("openid")
    if not openid:
        return error_response(code=400, msg="获取openid失败")
    
    # 查询教师记录
    teacher = execute_query(
        "SELECT id, org_id FROM t_teacher WHERE openid = %s",
        (openid,),
        fetch_one=True
    )
    
    if not teacher:
        # 自动注册：创建机构 + 教师记录
        org_id = execute_write(
            "INSERT INTO t_organization (org_name, status) VALUES ('新机构', 1)"
        )
        teacher_id = execute_write(
            "INSERT INTO t_teacher (openid, org_id, phone, role) VALUES (%s, %s, '', 'admin')",
            (openid, org_id)
        )
        teacher = {"id": teacher_id, "org_id": org_id}
    
    token = create_access_token(openid=openid, org_id=teacher["org_id"])
    
    return success_response(
        data=LoginResponse(token=token, openid=openid, org_id=teacher["org_id"]).model_dump()
    )


# ==================== 机构管理接口 ====================
@router.post("/org")
@jwt_required
async def create_org(request: Request, req: CreateOrgRequest):
    """创建机构"""
    org_id = execute_write(
        "INSERT INTO t_organization (org_name, status) VALUES (%s, 1)",
        (req.org_name,)
    )
    return success_response(data={"id": org_id, "org_name": req.org_name}, msg="机构创建成功")


@router.get("/org/info")
@jwt_required
async def get_org_info(request: Request):
    """获取当前机构信息"""
    org_id = get_current_org_id(request)
    org = execute_query(
        "SELECT id, org_name, status, created_at FROM t_organization WHERE id = %s AND status = 1",
        (org_id,),
        fetch_one=True
    )
    if not org:
        return error_response(code=404, msg="机构不存在或已被禁用")
    return success_response(data=OrgInfo(**org).model_dump())


# ==================== 班级管理接口 ====================
@router.post("/class")
@jwt_required
async def create_class(request: Request, class_req: CreateClassRequest):
    """创建班级"""
    org_id = get_current_org_id(request)
    
    # 校验机构存在
    org = execute_query("SELECT id FROM t_organization WHERE id = %s AND status = 1", (org_id,), fetch_one=True)
    if not org:
        return error_response(code=404, msg="机构不存在或已被禁用")
    
    class_id = execute_write(
        "INSERT INTO t_class (org_id, class_name, teacher_name) VALUES (%s, %s, %s)",
        (org_id, class_req.class_name, class_req.teacher_name or "")
    )
    
    return success_response(data={"id": class_id}, msg="班级创建成功")


@router.get("/class/list")
@jwt_required
async def get_class_list(request: Request):
    """查询当前机构的班级列表"""
    org_id = get_current_org_id(request)
    
    classes = execute_query(
        """
        SELECT id, org_id, class_name, teacher_name, created_at 
        FROM t_class WHERE org_id = %s ORDER BY created_at DESC
        """,
        (org_id,)
    )
    
    return success_response(data={
        "total": len(classes),
        "list": [ClassInfo(**c).model_dump() for c in classes]
    })


# ==================== 教师管理接口 ====================
@router.get("/teacher/info")
@jwt_required
async def get_teacher_info(request: Request):
    """获取当前教师信息"""
    openid = get_current_openid(request)
    org_id = get_current_org_id(request)
    
    teacher = execute_query(
        """
        SELECT id, openid, org_id, class_id, phone, role, created_at 
        FROM t_teacher WHERE openid = %s AND org_id = %s
        """,
        (openid, org_id),
        fetch_one=True
    )
    
    if not teacher:
        return error_response(code=404, msg="教师信息不存在")
    
    return success_response(data=teacher)


@router.put("/teacher/bind-class")
@jwt_required
async def bind_class(request: Request, bind_req: BindClassRequest):
    """教师绑定班级（加入班级）"""
    openid = get_current_openid(request)
    org_id = get_current_org_id(request)
    
    # 校验班级属于当前机构
    cls = execute_query(
        "SELECT id FROM t_class WHERE id = %s AND org_id = %s",
        (bind_req.class_id, org_id),
        fetch_one=True
    )
    if not cls:
        return error_response(code=404, msg="班级不存在或不属于当前机构")
    
    execute_write(
        "UPDATE t_teacher SET class_id = %s WHERE openid = %s AND org_id = %s",
        (bind_req.class_id, openid, org_id)
    )
    
    return success_response(msg=f"已绑定到班级 ID={bind_req.class_id}")


@router.put("/teacher/profile")
@jwt_required
async def update_teacher_profile(request: Request, profile_req: UpdateTeacherRequest):
    """更新教师资料（手机号等）"""
    openid = get_current_openid(request)
    org_id = get_current_org_id(request)
    
    updates = []
    params = []
    
    if profile_req.phone is not None:
        updates.append("phone = %s")
        params.append(profile_req.phone)
    if profile_req.class_id is not None:
        # 校验班级存在且属于当前机构
        cls = execute_query("SELECT id FROM t_class WHERE id = %s AND org_id = %s", (profile_req.class_id, org_id), fetch_one=True)
        if not cls:
            return error_response(code=404, msg="目标班级不存在")
        updates.append("class_id = %s")
        params.append(profile_req.class_id)
    
    if not updates:
        return error_response(code=400, msg="没有需要更新的字段")
    
    params.extend([openid, org_id])
    execute_write(f"UPDATE t_teacher SET {', '.join(updates)} WHERE openid = %s AND org_id = %s", tuple(params))
    
    return success_response(msg="资料更新成功")
