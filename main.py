"""FastAPI应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router
from init_db import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时自动初始化数据库"""
    print("正在初始化数据库...")
    init_database()
    print("服务启动完成")
    yield
    print("服务关闭")


app = FastAPI(
    title="多租户机构管理API",
    description="基于FastAPI的多租户机构管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "多租户机构管理系统API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
