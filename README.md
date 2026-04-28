# 家校互通平台 - 后端服务

基于 **FastAPI + SQLAlchemy (async) + MySQL** 的家校互通系统后端，支持机构端小程序、家长端小程序、运营管理Web端。

---

## 项目结构

```
backend/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── core/
│   │   ├── config.py            # 环境变量配置 (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy 异步引擎 + Base模型(含id/created_at/updated_at/is_delete)
│   │   ├── security.py          # JWT认证 + bcrypt密码加密 + 三种角色定义
│   │   ├── deps.py              # 依赖注入: get_current_user / require_roles 角色鉴权
│   │   └── response.py          # 统一返回格式 {"code":0, "msg":"success", "data":{}}
│   ├── models/
│   │   └── models.py            # 6张表ORM模型 (多租户 institution_id 隔离)
│   ├── schemas/
│   │   └── institution.py       # Pydantic 请求/响应 Schema
│   ├── services/
│   │   └── institution.py       # 机构注册/查询/审核 业务逻辑层
│   └── api/
│       ├── health.py            # GET /api/health 健康检查
│       └── platform/
│           └── institution.py   # 机构管理API (注册/列表/审核)
├── Dockerfile                   # 容器化构建文件
├── .dockerignore                # Docker 构建排除项
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
docker-compose.yml               # MySQL 8.0 + FastAPI 编排
```

---

## 已完成任务

### 任务1 - FastAPI 项目基础框架
- SQLAlchemy 异步连接 MySQL（环境变量读取配置）
- JWT 认证体系（三种角色：`platform_admin` / `principal` / `teacher`）
- CORS 中间件、请求耗时统计、全局异常捕获
- 统一返回格式 `{"code": 0, "msg": "success", "data": {}}`
- `/api/health` 健康检查接口

### 任务2 - 企业级数据库模型（多租户）
6 张核心业务表：

| 表名 | 说明 | 多租户 |
|------|------|--------|
| `platform_admin` | 平台管理员 | - |
| `institution` | 机构（含人脸功能开关） | - |
| `org_user` | 机构用户（校长/教师） | ✅ institution_id |
| `class` | 班级 | ✅ institution_id |
| `student` | 学员（预留 face_image_url） | ✅ institution_id |
| `attendance_record` | 考勤记录 | ✅ institution_id |

- 所有表继承 `Base`（自动包含 `id`, `created_at`, `updated_at`, `is_delete` 软删除字段）

### 任务3 - 机构注册与审核 API（运营管理端）
3 个接口：

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/platform/institutions/` | 无需认证 | 提交机构注册申请 |
| GET | `/api/platform/institutions/` | platform_admin | 机构列表（分页/状态/关键词筛选） |
| PUT | `/api/platform/institutions/{id}/review` | platform_admin | 审批机构（通过后自动创建校长账号） |

**审核通过自动创建校长账号规则：**
- 登录账号 = 机构的 `contact_phone`（手机号）
- 默认密码 = 手机号 **后4位**
- 角色 = `principal`

---

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 复制并编辑环境变量
cp backend/.env.example .env
# 编辑 .env 填写你的 MySQL 密码等信息

# 2. 启动服务（MySQL + API 会自动启动）
docker compose up -d --build

# 3. 查看日志
docker compose logs -f api

# 4. 验证服务
curl http://localhost:8080/api/health
```

### 方式二：本地开发

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv venv && source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接信息

# 4. 确保本地 MySQL 已运行，然后启动
python -m app.main
# 或使用 uvicorn:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000/docs 查看 Swagger 文档。

---

## 接口测试指南

### 前置准备

#### 1. 初始化数据库

确保 MySQL 中已创建数据库和表结构。可参考 `schema.sql` 或手动执行：

```sql
CREATE DATABASE IF NOT EXISTS school_comm DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

如果使用了 docker-compose 且挂载了 `schema.sql`，容器会自动初始化。

#### 2. 创建平台管理员（用于获取 Token）

在 MySQL 中执行：

```sql
-- 使用 bcrypt 生成密码哈希（或用 Python 快速生成）
-- python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('admin123'))"

INSERT INTO platform_admin (username, password_hash) VALUES
('admin', '$2b$12$你的bcrypt哈希值');
```

> **快速生成密码哈希命令**（Python 环境）：
> ```bash
> python3 -c "
> from passlib.context import CryptContext
> ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
> print(ctx.hash('admin123'))
> "
> ```

#### 3. 获取管理员 JWT Token

使用 Postman 或 curl 发送登录请求（需要先有登录接口，或手动构造 Token 用于测试）：

```bash
# 临时方式：用 Python 手动生成一个测试 token
python3 -c "
from app.core.security import create_access_token
token = create_access_token({'sub': '1', 'role': 'platform_admin'})
print(token)
"
```

> 如果还没有登录接口，可以在 Python 中运行上面的代码生成测试 Token。

---

### Postman 测试步骤

#### Step 1: 测试健康检查（无需任何准备）

```
GET http://localhost:8080/api/health
```

**预期响应：**
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "status": "ok",
        "service": "家校互通平台",
        "version": "1.0.0"
    },
    "timestamp": "2025-xx-xx xx:xx:xx"
}
```

---

#### Step 2: 提交机构注册申请（无需Token）

```
POST http://localhost:8080/api/platform/institutions/

Content-Type: application/json

{
    "name": "阳光幼儿园",
    "contact_person": "张老师",
    "contact_phone": "13800138001",
    "address": "北京市海淀区中关村大街1号"
}
```

**预期响应：**
```json
{
    "code": 0,
    "msg": "注册申请已提交，请等待审核",
    "data": {
        "id": 1,
        "name": "阳光幼儿园"
    }
}
```

**验证数据库：**
```sql
SELECT id, name, contact_phone, status FROM institution WHERE is_delete = 0;
-- 应看到 status=0 (待审核) 的记录
```

---

#### Step 3: 查看机构列表（需要管理员Token）

**先设置 Authorization Header：**

```
Key: Authorization
Value: Bearer <你的JWT_TOKEN>
```

然后发送：
```
GET http://localhost:8080/api/platform/institutions/?page=1&page_size=10&status=0
```

可选参数：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页数量 |
| `status` | int | null | 0=待审核 1=已通过 2=已拒绝 |
| `keyword` | string | null | 搜索名称/手机号 |

**预期响应（成功）：**
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "name": "阳光幼儿园",
                "contact_person": "张老师",
                "contact_phone": "13800138001",
                "address": "北京市海淀区中关村大街1号",
                "status": 0,
                "face_enabled": false,
                "face_expire_date": null,
                "created_at": "..."
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1
    }
}
```

**未携带Token / Token无效时返回 401：**
```json
{"detail": "未提供认证令牌"}
```

---

#### Step 4: 审核机构 - 通过（需要管理员Token）

```
PUT http://localhost:8080/api/platform/institutions/1/review

Authorization: Bearer <你的JWT_TOKEN>
Content-Type: application/json

{
    "status": 1,
    "remark": "审核通过"
}
```

**预期响应：**
```json
{
    "code": 0,
    "msg": "审核通过，管理员账号已创建",
    "data": {
        "institution_id": 1,
        "status": 1,
        "principal_account": "13800138001",
        "default_password": "0***1",
        "message": "审核通过，管理员账号已创建"
    }
}
```

**验证数据库（应同时更新两张表）：**
```sql
-- 1. 机构状态变为已通过
SELECT id, name, status FROM institution WHERE id = 1;
-- status = 1

-- 2. 自动创建了校长账号
SELECT id, institution_id, name, phone, role, password_hash
FROM org_user WHERE institution_id = 1 AND role = 'principal';
-- 应看到一条 principal 记录，phone = 13800138001
-- 默认密码为手机后4位: 8001
```

---

#### Step 5: 测试拒绝审核

再注册一个机构（重复 Step 2），然后用另一个ID进行拒绝：

```
PUT http://localhost:8080/api/platform/institutions/2/review

Authorization: Bearer <你的JWT_TOKEN>
Content-Type: application/json

{
    "status": 2,
    "remark": "资料不完整，请补充"
}
```

**预期响应：**
```json
{
    "code": 0,
    "msg": "已拒绝该机构的注册申请",
    "data": {
        "institution_id": 2,
        "status": 2,
        "principal_account": null,
        "default_password": null,
        "message": "已拒绝该机构的注册申请"
    }
}
```

---

## Postman Collection 导入

可在 Postman 中新建以下请求保存为 Collection：

| 请求名 | 方法 | URL | Header |
|--------|------|-----|--------|
| Health Check | GET | `{{base_url}}/api/health` | 无 |
| Register Institution | POST | `{{base_url}}/api/platform/institutions/` | Content-Type: application/json |
| List Institutions | GET | `{{base_url}}/api/platform/institutions/` | Authorization: Bearer `{{token}}` |
| Review Institution | PUT | `{{base_url}}/api/platform/institutions/{{id}}/review` | Authorization: Bearer `{{token}}` |

建议在 Postman 中设置 Variables：
- `base_url`: `http://localhost:8080`
- `token`: 你的 JWT Token
- `id`: 机构 ID（用于审核接口）
