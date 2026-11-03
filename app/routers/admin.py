#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/27 All rights reserved.
"""
Project Name: myinfo,
File Name: admin.py,
IDE: PyCharm,
Day: 2026 - 10 - 27,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.core.dependencies import get_current_admin, get_db, get_current_user, generate_pwd, check_pwd, create_token
from app.core.models import Users, UserInfo
from app.core.schemas import UserOut, UserCreate, UserLogin, TokenOut, PageResponse, UserUpdate
from app.utils.logger import write_operation_log
from app.utils.mypagination import paginate


router = APIRouter()


@router.get("/", response_model=PageResponse[UserOut], status_code=200)
async def show_users(
        page: int = Query(1, ge=1, description='页码'),
        page_size: int = Query(10, ge=1, le=100, description='每页显示的数量'),
        _current_user_admin: Users = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Users).where(Users.status == True).order_by(Users.create_time.desc())
    return await paginate(db, stmt, page, page_size)


@router.get('/me', response_model=UserOut, status_code=200)
async def show_me(
        current_user: Users = Depends(get_current_user)
):
    return current_user


@router.post('/register', response_model=UserOut, status_code=201)
async def register(
        background_tasks: BackgroundTasks,
        request: Request,
        create_user: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Users).where(Users.username == create_user.username, Users.status == True)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='用户已存在!')

    new_user = Users(
        username=create_user.username,
        password_hash=generate_pwd(create_user.password)
    )
    new_info = UserInfo(**create_user.userinfo.model_dump())
    new_user.userinfo = new_info
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=new_user.id,
        username=new_user.username,
        action='REGISTER',
        resource='USER',
        resource_id=new_user.id,
        detail={'message': f'用户{new_user.username}注册成功，密码为:xxxxxxxx'},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )
    return new_user


@router.post('/login', response_model=TokenOut, status_code=200)
async def login(
        background_tasks: BackgroundTasks,
        request: Request,
        login_user: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Users).where(Users.username == login_user.username, Users.status == True)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None or not check_pwd(login_user.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误！')

    token = {
        'sub': login_user.username,
    }
    access_token = create_token(token)
    background_tasks.add_task(
        write_operation_log,
        user_id=user.id,
        username=login_user.username,
        action='LOGIN',
        resource='USER',
        resource_id=user.id,
        detail={'message': f'用户{login_user.username}[admin:{user.is_admin}]登录成功!'},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )
    return {'access_token': access_token, 'token_type': 'bearer', 'is_admin': user.is_admin}


@router.patch('/{users_id}', response_model=UserOut, status_code=200)
async def update_user(
        users_id: int,
        user_in: UserUpdate,
        request: Request,
        background_tasks: BackgroundTasks,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    if users_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='你没有权限修改该用户的信息!')

    user = (await db.execute(select(Users).where(Users.id == users_id).options(selectinload(Users.userinfo)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='该用户不存在或已被删除!')

    if user_in.password:
        user.password_hash = generate_pwd(user_in.password)
    update_data = user_in.model_dump(exclude_unset=True, exclude={'password', 'userinfo'})
    for key, value in update_data.items():
        setattr(user, key, value)
    # 如果更新了用户详细信息
    if user_in.userinfo:
        info_data = user_in.userinfo.model_dump(exclude_unset=True)
        if user.userinfo is None:
            new_info = UserInfo(**info_data, users_id=user.id)
            user.userinfo = new_info
        else:
            for key, value in info_data.items():
                setattr(user.userinfo, key, value)
    # 处理账号状态
    if user_in.status is not None:
        user.status = user_in.status
        if user_in.status is False:
            user.del_time = datetime.now()
        else:
            user.del_time = None

    db.add(user)
    await db.commit()
    await db.refresh(user)
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user.id,
        username=current_user.username,
        action='UPDATE',
        resource='USER',
        resource_id=user.id,
        detail={'data': user_in.model_dump(exclude_unset=True, exclude={'password'})},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )

    return user


@router.delete('/{user_id}', status_code=200)
async def delete_user(
        user_id: int,
        request: Request,
        background_tasks: BackgroundTasks,
        current_user_admin: Users = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    # 💡 核心防御：防止管理员把自己删了
    if current_user_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='不能删除当前登录的账号！'
        )

    stmt = select(Users).where(Users.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='用户不存在')
    if user.status is False or user.del_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='用户已被删除或注销')

    user.status = False
    user.del_time = datetime.now()

    await db.commit()
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user_admin.id,
        username=current_user_admin.username,
        action='DELETE',
        resource='USER',
        resource_id=user.id,
        detail={'message': f'Log:{current_user_admin.username}删除了用户{user.username}'},
        ip_address= request.client.host if request.client else 'UNKNOWN IP',
    )
    return {'message': '删除成功'}