#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/29 All rights reserved.
"""
Project Name: myinfo,
File Name: mypagination.py,
IDE: PyCharm,
Day: 2026 - 10 - 29,
Author: Jinjing.Liu
Title:
Description:自定义分页
    1.
    2.
"""
from typing import Any, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
        db: AsyncSession,
        stmt,
        page: int,
        page_size: int
) -> Dict[str, Any]:
    # 查询总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0
    # 计算总页数 (纯整数向上取整)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    # 查询数据
    offset = (page - 1) * page_size

    paginated_stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(paginated_stmt)
    items = result.scalars().all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }
