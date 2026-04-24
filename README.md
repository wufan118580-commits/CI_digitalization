# 多租户机构管理 API

基于 FastAPI 的多租户机构管理系统，支持微信小程序登录。

## 技术栈

- **后端框架**: FastAPI + Uvicorn
- **数据库**: PyMySQL（原生 SQL）
- **认证**: JWT (python-jose)
- **部署**: Docker + GitHub Actions
- **镜像源**: 清华 pip 源 + 腾讯云镜像加速

## 项目结构

```
/workspace/
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD 部署配置
├── schema.sql              # 数据库建表参考
├── init_db.py              # 自动建表（启动时执行）
├── requirements.txt        # Python 依赖
├── config.py               # 配置文件
├── database.py             # 数据库连接工具
├── auth.py                 # JWT 认证装饰器
├── response.py             # 统一响应格式
├── models.py               # Pydantic 模型
├── router.py               # API 路由（8个接口）
├── main.py                 # FastAPI 应用入口
├── Dockerfile              # Docker 镜像构建
├── docker-compose.yml      # Docker Compose 编排
└── nginx.conf              # Nginx 反向代理配置
```

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `t_organization` | 机构表 |
| `t_class` | 班级表 |
| `t_teacher` | 教师表 |

## API 接口

| 分类 | 接口 | 方法 | 鉴权 | 说明 |
|------|------|------|------|------|
| **认证** | `POST /api/login` | 否 | 微信登录，自动注册，返回 JWT token |
| **机构** | `POST /api/org` | 是 | 创建机构 |
| **机构** | `GET /api/org/info` | 是 | 获取当前机构信息 |
| **班级** | `POST /api/class` | 是 | 创建班级（自动填充 org_id） |
| **班级** | `GET /api/class/list` | 是 | 查询当前机构的班级列表 |
| **教师** | `GET /api/teacher/info` | 是 | 获取当前教师信息 |
| **教师** | `PUT /api/teacher/bind-class` | 是 | 教师绑定班级 |
| **教师** | `PUT /api/teacher/profile` | 是 | 更新教师资料（手机号等） |

### 业务流程

```
管理员操作:
  POST /api/login → 获取 token
    ↓
  POST /api/org → 创建机构
    ↓
  POST /api/class → 创建班级（可多个）
    ↓
  分享给老师

教师操作:
  POST /api/login → 自动注册/登录
    ↓
  PUT /api/teacher/bind-class → 绑定班级
    ↓
  GET /api/class/list → 查看所在班级
```

## 统一响应格式

```json
{
  "code": 200,
  "data": {},
  "msg": ""
}
```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp .env.example .env
# 编辑 .env 填写配置

# 初始化数据库
mysql -u root -p < schema.sql

# 运行服务
python main.py
```

## 部署架构

```
GitHub (develop 分支)
    ↓ push
GitHub Actions
    ├─ 测试 (MySQL)
    └─ SSH 部署到服务器
            ↓
        服务器 (Docker)
            ├─ git clone 代码
            ├─ docker build (清华源)
            └─ docker run -p 8080:8080
                    ↓
            云数据库 (内网连接)
```

## Git 工作流

1. `develop` 分支：开发测试 → 自动部署到预发布环境 (8081)
2. `PR → main` 分支：合并后自动部署到生产环境 (8080)

## 已完成功能

- [x] 微信小程序登录 + 自动注册 (POST /api/login)
- [x] JWT Token 生成与验证
- [x] JWT 鉴权装饰器 (@jwt_required)
- [x] 多租户数据隔离 (每个 SQL 包含 WHERE org_id = %s)
- [x] 机构管理：创建机构、查询信息
- [x] 班级管理：创建班级、查询列表
- [x] 教师管理：获取信息、绑定班级、更新资料
- [x] 应用启动自动建表 (init_db.py)
- [x] 统一响应格式
- [x] PyMySQL 原生 SQL 操作
- [x] Docker 镜像构建 (host 网络模式)
- [x] GitHub Actions CI/CD 流程 (Docker Compose 部署)

## 待完成

- [ ] 编写单元测试
- [ ] 日志配置与收集
- [ ] 限流与安全防护
- [ ] Web 管理后台（当前仅 API）

## 测试指南

### 部署验证

```bash
# SSH 到服务器后执行
curl http://localhost:8080/health
# 预期: {"status":"ok"}
```

### API 测试（无需微信小程序）

```bash
# 1. 生成测试 Token（本地执行）
python generate_test_token.py

# 2. 测试创建班级
curl -X POST http://服务器IP:8080/api/class \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的token" \
  -d '{"class_name": "一年级一班", "teacher_name": "张三"}'

# 3. 测试查询班级列表
curl http://服务器IP:8080/api/class/list \
  -H "Authorization: Bearer 你的token"

# 4. 预期响应
{"code": 200, "data": {"total": 1, "list": [{"id": 1, "org_id": 1, "class_name": "一年级一班", ...}]}, "msg": "success"}
```

### Postman 测试

1. 下载 [Postman](https://www.postman.com/)
2. 导入 API 地址：`http://你的服务器IP:8080`
3. 访问 `/docs` 查看 Swagger 文档（需开放 8080 端口）

### 准备测试数据

```sql
-- 手动插入测试数据到云数据库
INSERT INTO t_organization (org_name, status) VALUES ('测试机构', 1);

-- 重要：确保 t_teacher 表有对应记录，登录才能获取 org_id
INSERT INTO t_teacher (openid, org_id, phone, role) 
VALUES ('test_openid_123', 1, '13800138000', 'admin');
```

## 注意事项

- MySQL 5.7 完全兼容
- 服务器需开放 8080 端口（或通过 Nginx 80 端口代理）
- 测试 Token 仅用于开发调试，生产环境请删除 `generate_test_token.py`
