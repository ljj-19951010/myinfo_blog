#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026/10/27 All rights reserved.
"""
Project Name: myinfo,
File Name: config.py,
IDE: PyCharm,
Day: 2026 - 10 - 27,
Author: Jinjing.Liu
Title:
Description:
    1.
    2.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    POOL_SIZE: int = 5
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    MAX_OVERFLOW: int = 10

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


settings = Settings()

