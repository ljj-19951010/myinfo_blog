#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/11/3 All rights reserved.
"""
Project Name: myinfo,
File Name: test_api.py,
IDE: PyCharm,
Day: 2026 - 11 - 03,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
import pytest
from httpx import AsyncClient

# 标记为异步测试
pytestmark = pytest.mark.asyncio

async def test_health_check(async_client: AsyncClient):
    """测试健康检查接口"""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

async def test_register_and_login(async_client: AsyncClient):
    """测试注册和登录"""
    # 1. 测试注册
    reg_response = await async_client.post("/api/user/register", json={
        "username": "newuser",
        "password": "password123",
        "userinfo": {"name": "新用户"}
    })
    assert reg_response.status_code == 201
    assert reg_response.json()["username"] == "newuser"

    # 2. 测试重复注册（应报错）
    reg_dup = await async_client.post("/api/user/register", json={
        "username": "newuser",
        "password": "password123",
        "userinfo": {"name": "新用户"}
    })
    assert reg_dup.status_code == 400

    # 3. 测试登录
    login_response = await async_client.post("/api/user/login", json={
        "username": "newuser",
        "password": "password123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

async def test_create_article_unauthorized(async_client: AsyncClient):
    """测试未登录时发文章（应该拦截）"""
    response = await async_client.post("/api/articles/create_article", json={
        "title": "未授权文章",
        "content": "内容"
    })
    # 没带 Token，返回 401 Unauthorized（未认证）
    assert response.status_code == 401

async def test_create_article_success(async_client: AsyncClient, auth_token: str):
    """测试登录后成功发文章"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await async_client.post("/api/articles/create_article",
        headers=headers,
        json={
            "title": "FastAPI 入门",
            "content": "这是一篇测试文章的内容",
            "category": "后端开发"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "FastAPI 入门"
    assert data["author"]["username"] == "testuser"  # 验证作者信息被正确关联