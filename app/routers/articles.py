#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/11/2 All rights reserved.
"""
Project Name: myinfo,
File Name: articles.py,
IDE: PyCharm,
Day: 2026 - 11 - 02,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.core.dependencies import get_db, get_current_user
from app.core.models import Articles, Users, Comments
from app.core.schemas import ArticlesOut, PageResponse, ArticlesCreate, ArticlesUpdate, ArticleDetailOut, CommentsOut, \
    CommentsCreate
from app.utils.logger import write_operation_log
from app.utils.mypagination import paginate


router = APIRouter()

# 排序规则白名单
SORTABLE_FIELDS = {
        'category': Articles.category,
        'create_time': Articles.create_time,
        'follow': Articles.follow
    }

@router.get('/', response_model=PageResponse[ArticlesOut], status_code=200)
async def show_articles(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    查看所有数据，不包含已删除
    :param page:
    :param page_size:
    :param db:
    :return:
    """
    stmt = select(Articles).where(Articles.del_time.is_(None)).options(selectinload(Articles.author)).order_by(Articles.create_time.desc())
    return await paginate(db, stmt, page, page_size)


@router.get('/sorted', response_model=PageResponse[ArticlesOut], status_code=200)
async def sorted_articles(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        sort_by: str = Query('create_time'),
        order: str = Query('desc'),
        db: AsyncSession = Depends(get_db)
):
    """
    排序
    :param page:
    :param page_size:
    :param sort_by:
    :param order:
    :param db:
    :return:
    """
    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'不支持的排序，仅支持:{list(SORTABLE_FIELDS.keys())}')
    if order not in ['desc', 'asc']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'排序方向仅支持asc或desc')

    sort_field = SORTABLE_FIELDS[sort_by]
    if order == 'desc':
        order_clause = sort_field.desc()
    else:
        order_clause = sort_field.asc()

    stmt = select(Articles).where(Articles.del_time.is_(None)).options(selectinload(Articles.author)).order_by(order_clause)

    return await paginate(db, stmt, page, page_size)


@router.get('/search', response_model=PageResponse[ArticlesOut], status_code=200)
async def search_articles(
        keywords: Optional[str] = Query(None, description='关键字'),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    搜索
    :param keywords:
    :param page:
    :param page_size:
    :param db:
    :return:
    """
    stmt = (select(Articles).where(Articles.del_time.is_(None)).outerjoin(Users, Articles.users_id == Users.id).options(selectinload(Articles.author)))
    if keywords:
        search_pattern = f'%{keywords.strip()}%'
        stmt = stmt.where(or_(
            Articles.title.ilike(search_pattern),
            Articles.content.ilike(search_pattern),
            Articles.category.ilike(search_pattern),
            Users.username.ilike(search_pattern)
        ))
    stmt = stmt.order_by(Articles.create_time.desc())

    return await paginate(db, stmt, page, page_size)


@router.post('/create_article', response_model=ArticlesOut, status_code=201)
async def create_article(
        background_tasks: BackgroundTasks,
        request: Request,
        article_in: ArticlesCreate,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    添加文章，标题或内容不可以重复。因为标题和内容重复了 说明是复制的别人的。不允许
    :param article_in:
    :param current_user:
    :param db:
    :return:
    """
    base_stmt = select(Articles).where(Articles.del_time.is_(None)).options(selectinload(Articles.author))
    stmt = base_stmt.where(Articles.title == article_in.title, Articles.content == article_in.content)
    article = (await db.execute(stmt)).scalar_one_or_none()
    if article:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='标题或内容已存在!')
    new_article = Articles(
        title=article_in.title,
        content=article_in.content,
        category=article_in.category,
        description=article_in.description,
        users_id=current_user.id
    )
    new_article.author = current_user

    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user.id,
        username=current_user.username,
        action='CREATE',
        resource='Articles',
        resource_id=new_article.id,
        detail={'data': ArticlesOut.model_validate(new_article).model_dump(mode='json'), 'message': f'用户{current_user.username}创建文章<<{new_article.title}>>成功!'},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )
    return new_article


@router.patch('/{article_id}', response_model=ArticlesOut, status_code=200)
async def update_article(
        background_tasks: BackgroundTasks,
        request: Request,
        article_id: int,
        article_in: ArticlesUpdate,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    patch局部更新，前端传了什么我再改什么，put是全部更新，前端必须传入全部字段
    :param article_id:
    :param article_in:
    :param current_user:
    :param db:
    :return:
    """
    base_stmt = select(Articles).where(Articles.id == article_id, Articles.del_time.is_(None)).options(selectinload(Articles.author))
    article = (await db.execute(base_stmt)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='该文章不存在或已被删除')
    if article.users_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='你没有权限修改该文章')

    update_data = article_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)
    await db.commit()
    await db.refresh(article)
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user.id,
        username=current_user.username,
        action='UPDATE',
        resource='Articles',
        resource_id=article.id,
        detail={'data':article_in.model_dump(exclude_unset=True)},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )
    return article


@router.delete('/{article_id}', status_code=200)
async def delete_article(
        background_tasks: BackgroundTasks,
        request: Request,
        article_id: int,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    删除
    :param article_id:
    :param current_user:
    :param db:
    :return:
    """
    stmt = select(Articles).where(Articles.id == article_id, Articles.del_time.is_(None))
    article = (await db.execute(stmt)).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail='文章不存在')

    if article.users_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail='权限不足')

    # 软删除
    article.del_time = datetime.now()
    await db.commit()
    # 写入日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user.id,
        username=current_user.username,
        action='DELETE',
        resource='Articles',
        resource_id=article.id,
        detail={'message': f'用户{current_user.username}删除了标题是{article.title},id为{article.id}的文章'},
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )
    return {"message": "文章已删除"}


# 文章详细
@router.get('/{article_id}', response_model=ArticleDetailOut, status_code=200)
async def get_article_detail(
        article_id: int,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Articles).where(Articles.id == article_id, Articles.del_time.is_(None)).options(
        selectinload(Articles.author),
        selectinload(Articles.comments).selectinload(Comments.user)
    )
    article = (await db.execute(stmt)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='文章不存在')
    return article


# 发表评论
@router.post('/{article_id}/comments', response_model=CommentsOut, status_code=200)
async def create_comments(
        article_id: int,
        comment_in: CommentsCreate,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    stmt = select(Articles).where(Articles.id == article_id, Articles.del_time.is_(None))
    article = (await db.execute(stmt)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='文章不存在')

    # 添加评论
    new_comment = Comments(
        content=comment_in.content,
        articles_id=article_id,
        users_id=current_user.id,
        parent_id=comment_in.parent_id
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


@router.delete('/{article_id}/comments/{comment_id}', status_code=200, tags=['comments'])
async def delete_comment(
        article_id: int,
        comment_id: int,
        request: Request,
        background_tasks: BackgroundTasks,
        current_user: Users = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # 1. 查当前要删除的评论
    stmt = select(Comments).where(
        Comments.id == comment_id,
        Comments.articles_id == article_id,
        Comments.del_time.is_(None)
    )
    target_comment = (await db.execute(stmt)).scalar_one_or_none()

    if not target_comment:
        raise HTTPException(status_code=404, detail='该评论不存在或已被删除')

    # 2. 权限校验
    if target_comment.users_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail='权限不足，只能删除自己的评论')

    # 3. 核心逻辑：查出这篇文章下所有未被删除的评论，在内存中构建树，收集所有子孙节点的 ID
    # 💡 为什么在内存里做？因为评论数据量不会像文章那么大，一次性拉出来构建父子关系远比写复杂的 SQL 递归 CTE 简单且兼容性极好。
    all_comments_stmt = select(Comments.id, Comments.parent_id).where(
        Comments.articles_id == article_id,
        Comments.del_time.is_(None)
    )
    all_comments = (await db.execute(all_comments_stmt)).all()

    # 构建 {parent_id: [child_id1, child_id2]} 的映射表
    children_map = {}
    for cid, pid in all_comments:
        if pid not in children_map:
            children_map[pid] = []
        children_map[pid].append(cid)

    # 广度优先搜索（BFS）收集所有需要删除的 ID
    ids_to_delete = []
    queue = [comment_id]

    while queue:
        current_id = queue.pop(0)
        ids_to_delete.append(current_id)
        # 如果这个评论有子评论，把子评论也加入队列，继续往下找
        if current_id in children_map:
            queue.extend(children_map[current_id])

    # 4. 执行批量软删除（一次性更新所有相关评论）
    now = datetime.now()
    update_stmt = (
        update(Comments)
        .where(Comments.id.in_(ids_to_delete))
        .values(del_time=now, status=False)
    )
    await db.execute(update_stmt)
    await db.commit()

    # 5. 异步记录日志
    background_tasks.add_task(
        write_operation_log,
        user_id=current_user.id,
        username=current_user.username,
        action='DELETE',
        resource='COMMENT',
        resource_id=comment_id,
        detail={
            'message': f'用户 {current_user.username} 删除了评论，级联删除了 {len(ids_to_delete) - 1} 条子回复。',
            'target_content': target_comment.content[:20]
        },
        ip_address=request.client.host if request.client else 'UNKNOWN IP'
    )

    return {"message": f"评论及其所有回复已删除，共影响 {len(ids_to_delete)} 条记录"}