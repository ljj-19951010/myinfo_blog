from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.routers import admin, articles


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title='My Blog',
    version='1.0.0',
    description='基于FastAPI + sqlalchemy + MYSQL开发后端接口文档',
    docs_url='/docs' if settings.DEBUG else None,
    redoc_url='/redoc' if settings.DEBUG else None,
    lifespan=lifespan
)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(admin.router, prefix='/api/user', tags=['User'])
app.include_router(articles.router, prefix='/api/articles', tags=['Articles'])


# 全局异常处理
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'message': '服务器内部错误!请联系IT处理。'},
    )

@app.get('/health', tags=['health'])
async def health():

    return {'status': 'ok', 'version': app.version}