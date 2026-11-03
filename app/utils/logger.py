#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/11/3 All rights reserved.
"""
Project Name: myinfo,
File Name: logger.py,
IDE: PyCharm,
Day: 2026 - 11 - 03,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from typing import Optional

from app.core.database import AsyncSessionLocal
from app.core.models import OperationLog


async def write_operation_log(
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        resource: str,
        resource_id: int,
        detail: Optional[dict] = None,
        ip_address: Optional[str] = None,
):
    async with AsyncSessionLocal() as session:
        try:
            log = OperationLog(
                user_id=user_id,
                username=username,
                action=action,
                resource=resource,
                resource_id=resource_id,
                detail=detail,
                ip_address=ip_address,
            )
            session.add(log)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f'日志写入失败:{e}')
