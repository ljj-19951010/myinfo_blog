#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/27 All rights reserved.
"""
Project Name: myinfo,
File Name: dependencies.py,
IDE: PyCharm,
Day: 2026 - 10 - 27,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from datetime import timedelta, datetime, timezone
from typing import AsyncGenerator, Optional, Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.models import Users


# 加密方式
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
credential = HTTPBearer()


# 创建会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 密码加密
def generate_pwd(password: str) -> str:
    return pwd_context.hash(password)


# 检查密码
def check_pwd(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


# 创建token
def create_token(data: dict, expire_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# 检查token
def check_token(token: str) -> Optional[Dict[str, Any]]:
    print(f'token是:{token}')
    try:
        payload  = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        if 'sub' not in payload:
            return None
        return payload
    except JWTError as jwt_error:
        print(f"JWT Token Error:{jwt_error}")
        return None


# 获取当前用户
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(credential),
        db: AsyncSession = Depends(get_db),
) -> Users:
    token = credentials.credentials
    payload = check_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效的凭据')
    username = payload.get('sub')
    result = await db.execute(select(Users).where(Users.username == username, Users.status == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户不存在')
    if not user.status:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='用户已注销或已被禁用')
    return user


# 获取当前用户是否为管理员用户
async def get_current_admin(
        current_user: Users = Depends(get_current_user)
) -> Users:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='你不是管理员账户!')
    return current_user
