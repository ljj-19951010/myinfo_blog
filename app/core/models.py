#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/27 All rights reserved.
"""
Project Name: myinfo,
File Name: models.py,
IDE: PyCharm,
Day: 2026 - 10 - 27,
Author: Jinjing.Liu
Title:
Description:使用逻辑外键而非物理外键
    1. 互联网大公司都是这样做的，禁止物理外键，为了程序的性能和架构的扩展性
    2. 物理外键在写入数据时会触发额外的父表查询和锁的竞争，在高并发下影响性能。
    3. 更重要的是，一旦需要分库或者分表操作物理外键就彻底失效
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, String, Boolean, DateTime, func, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment='用户名')
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment='密码哈希')
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment='状态: 1正常 0注销')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否管理员: 1是 0否')
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment='创建时间')
    del_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment='注销时间(软删除)')

    userinfo: Mapped[Optional["UserInfo"]] = relationship("UserInfo", back_populates="user", uselist=False, lazy='selectin', primaryjoin="Users.id == foreign(UserInfo.users_id)")
    articles: Mapped[List["Articles"]] = relationship("Articles", back_populates="author", primaryjoin="Users.id == foreign(Articles.users_id)")
    comments: Mapped[List["Comments"]] = relationship("Comments", back_populates="user", primaryjoin="Users.id == foreign(Comments.users_id)")

    __table_args__ = (
        {'comment': '用户表', 'mysql_charset': 'utf8mb4'}
    )


class UserInfo(Base):
    __tablename__ = 'user_info'

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True, comment='主键ID')
    name: Mapped[str] = mapped_column(String(50), comment='姓名', nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True, comment='邮箱')
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment='手机号')
    address: Mapped[Optional[str]] = mapped_column(String(255), comment='现住址')
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment='头像URL')
    id_card: Mapped[Optional[str]] = mapped_column(String(20), comment='身份证')
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment='创建时间')
    del_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment='软删除')

    users_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment='关联用户ID')
    user: Mapped[Optional["Users"]] = relationship("Users", back_populates="userinfo", primaryjoin="foreign(UserInfo.users_id) == Users.id")

    __table_args__ = (
        Index('idx_user_info_users_id', 'users_id'),
        {'comment': '用户信息表', 'mysql_charset': 'utf8mb4'}
    )


class Articles(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='文章标题')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='内容简述')
    content: Mapped[str] = mapped_column(Text, nullable=False, comment='内容')
    category: Mapped[Optional[str]] = mapped_column(String(255), comment='类别名称')
    follow: Mapped[Optional[int]] = mapped_column(BigInteger, default=0, comment='关注数')
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment='创建时间')
    del_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment='删除时间')

    # 作者逻辑外键
    users_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='作者ID')
    author: Mapped[Optional['Users']] = relationship("Users", back_populates="articles", lazy='selectin', primaryjoin="foreign(Articles.users_id) == Users.id")
    comments: Mapped[List["Comments"]] = relationship("Comments", back_populates="article", primaryjoin="Articles.id == foreign(Comments.articles_id)")

    __table_args__ = (
        Index('idx_articles_users_id', 'users_id'),
        {'comment': '文章表', 'mysql_charset': 'utf8mb4'}
    )


class Comments(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    content: Mapped[str] = mapped_column(Text, nullable=False, comment='评论内容')
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment='评论时间')
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment='状态: 1正常 0删除')
    del_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment='删除时间')

    # 逻辑外键：关联的文章ID
    articles_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='关联文章ID')
    # 逻辑外键：评论人ID (关联 Users 表)
    users_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='评论人ID')

    # 可选：如果支持楼中楼（回复某条评论），可以加 parent_id
    parent_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment='父评论ID(支持回复)')

    article: Mapped["Articles"] = relationship("Articles", back_populates="comments", primaryjoin="foreign(Comments.articles_id) == Articles.id")
    user: Mapped["Users"] = relationship("Users", back_populates="comments", primaryjoin="foreign(Comments.users_id) == Users.id")

    __table_args__ = (
        Index('idx_comments_articles_id', 'articles_id'),
        Index('idx_comments_users_id', 'users_id'),
        {'comment': '文章评论表', 'mysql_charset': 'utf8mb4'}
    )


class OperationLog(Base):
    __tablename__ = 'operation_log'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='主键id')
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, nullable=True, comment='操作人ID')
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment='操作人用户名')
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment='操作类型:create/update/delete')
    resource: Mapped[str] = mapped_column(String(50), nullable=False, comment='资源类型: articles/user')
    resource_id: Mapped[int] = mapped_column(BigInteger, comment='目标id')
    detail: Mapped[Optional[dict]] = mapped_column(JSON, comment='操作详细')
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), comment='操作人ip地址')
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment='操作时间')

    __table_args__ = (
        Index('idx_log_user_time','user_id', 'create_time'),
        {'comment': '业务操作日志表', 'mysql_charset': 'utf8mb4'}
    )
