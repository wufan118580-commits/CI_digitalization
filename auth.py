"""JWT认证工具"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from functools import wraps

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

# 安全方案
security = HTTPBearer()


class TokenData:
    """Token载荷数据"""
    def __init__(self, openid: str, org_id: int):
        self.openid = openid
        self.org_id = org_id


def create_access_token(openid: str, org_id: int) -> str:
    """创建JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {
        "openid": openid,
        "org_id": org_id,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解析JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        openid = payload.get("openid")
        org_id = payload.get("org_id")
        if openid is None or org_id is None:
            return None
        return TokenData(openid=openid, org_id=org_id)
    except JWTError:
        return None


def get_token_from_header(request: Request) -> str:
    """从请求头获取token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    return auth_header.replace("Bearer ", "")


def jwt_required(func):
    """JWT鉴权装饰器"""
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        token = get_token_from_header(request)
        token_data = decode_token(token)
        if token_data is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # 将token数据附加到request对象上
        request.state.token_data = token_data
        return await func(*args, request=request, **kwargs)
    return wrapper


def get_current_org_id(request: Request) -> int:
    """获取当前用户的org_id"""
    token_data: TokenData = request.state.token_data
    return token_data.org_id


def get_current_openid(request: Request) -> str:
    """获取当前用户的openid"""
    token_data: TokenData = request.state.token_data
    return token_data.openid
