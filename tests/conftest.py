#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/11/3 All rights reserved.
"""
Project Name: myinfo,
File Name: conftest.py,
IDE: PyCharm,
Day: 2026 - 11 - 03,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy import BigInteger, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base
from app.core.dependencies import get_db
from app.core import models

# 1. 创建内存 SQLite 引擎（StaticPool 保证多个连接共享同一个内存库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

# 2. 全局事件循环配置
@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 3. 初始化数据库（建表）
@pytest_asyncio.fixture(autouse=True)
async def init_db():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, BigInteger):
                column.type = Integer()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 4. 替换依赖，让测试走内存数据库
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# 5. 提供测试用的 HTTP 客户端
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    # 使用 ASGITransport 代替了 requests，直接测试 ASGI 应用
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

# 6. 提供一个已经注册并登录的用户 Token
@pytest_asyncio.fixture
async def auth_token(async_client: AsyncClient) -> str:
    # 注册
    await async_client.post("/api/user/register", json={
        "username": "testuser",
        "password": "testpassword",
        "userinfo": {"name": "测试用户", "email": "test@test.com"}
    })
    # 登录获取 Token
    response = await async_client.post("/api/user/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    return response.json()["access_token"]