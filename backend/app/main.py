from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import get_settings
from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models import Category
from app.routers import categories, dashboard, feedbacks, issues, session


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        category_count = db.scalar(select(func.count(Category.id))) or 0
        if category_count == 0:
            defaults = [
                ("功能异常", "已有功能报错、失效或结果不符合预期"),
                ("性能与稳定性", "响应慢、卡顿、崩溃或服务不可用"),
                ("易用性与交互", "流程复杂、提示不清或操作困难"),
                ("数据与内容", "数据错误、缺失、不同步或展示异常"),
                ("账号与权限", "登录、账号、角色、权限及访问问题"),
                ("产品需求", "新增功能、能力增强或业务场景建议"),
            ]
            db.add_all([
                Category(name=name, description=description, sort_order=index)
                for index, (name, description) in enumerate(defaults, start=1)
            ])
            db.commit()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(session.router, prefix="/api")
app.include_router(feedbacks.router, prefix="/api")
app.include_router(issues.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


def bundled_frontend_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "frontend_dist"
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


frontend_dir = bundled_frontend_dir()
if frontend_dir.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        requested = (frontend_dir / full_path).resolve()
        if requested.is_relative_to(frontend_dir.resolve()) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_dir / "index.html")
