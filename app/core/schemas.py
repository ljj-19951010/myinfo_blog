#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/27 All rights reserved.
"""
Project Name: myinfo,
File Name: schemas.py,
IDE: PyCharm,
Day: 2026 - 10 - 27,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from datetime import datetime
from typing import Optional, TypeVar, Generic, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field


T = TypeVar("T")

# token
class TokenOut(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool


# 分页
class PageResponse(BaseModel, Generic[T]):
    items: List[T]      # 数据列表
    total: int      # 总条数
    page: int       # 当前页码
    page_size: int       # 每页数量
    pages: int          # 总页数


# 用户信息
class UserInfoBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    id_card: Optional[str] = None


# 用户操作
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    userinfo: UserInfoBase


class UserOut(BaseModel):
    id: int
    username: str
    status: bool
    is_admin: bool
    userinfo: UserInfoBase

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(..., min_length=3, max_length=50)
    password: Optional[str] = Field(..., min_length=6)
    is_admin: Optional[bool] = None
    status: Optional[bool] = None
    userinfo: Optional[UserInfoBase] = None


class AuthorOut(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

# 文章管理
class ArticlesOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    category: Optional[str] = None
    follow: Optional[int] = 0
    create_time: datetime
    # 作者相关
    users_id: int
    author: Optional[AuthorOut] = None

    model_config = ConfigDict(from_attributes=True)


class ArticlesCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    category: Optional[str] = None


class ArticlesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


# 评论
class CommentUserOut(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)


class CommentsOut(BaseModel):
    id: int
    content: str
    create_time: datetime
    status: bool
    articles_id: int
    users_id: int
    parent_id: Optional[int] = None

    user: Optional[CommentUserOut] = None

    model_config = ConfigDict(from_attributes=True)


class CommentsCreate(BaseModel):
    content: str
    articles_id: int
    parent_id: Optional[int] = None


class ArticleDetailOut(ArticlesOut):
    # 💡 嵌套评论列表
    comments: List[CommentsOut] = []
