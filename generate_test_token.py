#!/usr/bin/env python3
"""生成测试用 JWT Token（仅用于测试）"""
from auth import create_access_token

# 修改这里的 org_id 为你的测试数据
openid = "test_openid_123"
org_id = 1

token = create_access_token(openid=openid, org_id=org_id)
print(f"\n测试 Token:")
print(f"OpenID: {openid}")
print(f"OrgID: {org_id}")
print(f"Token: {token}\n")
print(f"使用方式:")
print(f'curl -H "Authorization: Bearer {token}" http://localhost:8080/api/class/list')
