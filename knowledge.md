Secrets          config.py         .env / docker-compose
─────────       ─────────────      ──────────────────────
DB_HOST    →    DB_HOST           ✅ 匹配
DB_PORT    →    DB_PORT           ✅ 匹配
DB_USER    →    DB_USER           ✅ 匹配
DB_PASSWORD→    DB_PASSWORD       ✅ 匹配
DB_NAME    →    DB_NAME           ✅ 匹配
JWT_SECRET_KEY → SECRET_KEY        ✅ deploy.yml 写 .env 时映射
WECHAT_APPID  → WECHAT_APPID      ✅ 未来任务使用
WECHAT_SECRET → WECHAT_SECRET     ✅ 未来任务使用



前端永远不会接触到 JWT_SECRET_KEY。 这个密钥只在后端服务器内部使用。

正确的流程是这样的：
┌──────────┐                    ┌──────────────┐
│  前端     │                    │   后端服务器    │
│          │                    │              │
│ 1. 发送:  │ ──账号+密码──────→ │              │
│          │                    │ 2. 验证密码    │
│          │  ←──返回 token ── │ 3. 用密钥签名   │
│          │    (令牌)          │   生成token    │
│          │                    │              │
│ 4. 每次请求 │ ──带上 token ──→ │ 5. 用同一密钥  │
│          │                    │   验证token    │
│          │  ←──返回数据──── │   是否合法      │
└──────────┘                    └──────────────┘
                              内部保存着:
                           JWT_SECRET_KEY(绝不让出去)
