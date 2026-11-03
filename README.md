# 📝 My Blog Backend - FastAPI 个人博客后端系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg?style=flat-square)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg?style=flat-square)](https://www.sqlalchemy.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg?style=flat-square)](https://www.mysql.com/)
[![Pytest](https://img.shields.io/badge/Tested%20with-Pytest-yellow.svg?style=flat-square)](https://pytest.org/)

**一个基于 FastAPI + SQLAlchemy 2.0 (Async) + MySQL 构建的高性能、企业级个人博客后端 API。**

</div>

---

## 📖 项目简介 (Introduction)

本项目是从零搭建的个人博客后端系统。除了实现基础的博客增删改查功能外，项目在架构设计上严格遵循了现代互联网企业的开发规范，涵盖了 **JWT 鉴权、RBAC 权限控制、逻辑外键设计、异步高并发处理、业务操作审计、无限极评论树级联删除** 以及 **完整的 CI/自动化测试**。

## ✨ 核心特性 (Core Features)

- **现代化全异步架构**：基于 `asyncio`，全链路使用 FastAPI 的 `async def` 与 SQLAlchemy 2.0 异步引擎（`AsyncSession`），显著提升 I/O 密集型场景的并发能力。
- **严格的权限与安全控制**：
  - 基于 `OAuth2` 与 `JWT` 实现无状态认证。
  - 采用 `RBAC` 权限模型，通过依赖注入（`Depends`）在路由层拦截越权操作。
  - 利用 `Passlib (Argon2)` 进行高强度密码哈希。
  - 杜绝过度提交（Over-posting），Pydantic 严格隔离入参与出参。
- **企业级逻辑外键设计**：遵循大厂规范，摒弃数据库物理外键。通过应用层校验与 ORM `primaryjoin` 维护关联关系，为未来分库分表与高并发写入预留扩展性。
- **异步操作审计日志 (Audit Log)**：
  - 基于 FastAPI `BackgroundTasks` 在请求响应后异步写入。
  - 独立开启数据库 Session，确保日志写入失败绝不影响主业务事务。
  - 自动对敏感字段（如密码）进行脱敏处理。
- **无限极嵌套评论系统 (Nested Comments)**：
  - 支持楼中楼回复。在删除父评论时，通过内存构建树结构（BFS 广度优先搜索），实现无限极子评论的 **级联软删除**，避免孤儿数据。
- **性能调优**：彻底解决异步 ORM 环境下的 `MissingGreenlet` 与 `N+1` 查询问题（深度使用 `selectinload`），并封装了通用分页与动态排序组件。
- **高覆盖自动化测试**：基于 `Pytest` + `Httpx` + `SQLite 内存数据库` 的集成测试，保证核心链路（鉴权、发文、评论）的稳定性。

## 🛠 技术栈 (Tech Stack)

- **Python 环境**：Python 3.13+
- **核心框架**：FastAPI, Uvicorn
- **数据交互**：SQLAlchemy 2.0 (Async), Pydantic V2, Asyncmy
- **数据库**：MySQL 8.0, SQLite (用于测试)
- **数据库迁移**：Alembic
- **认证与安全**：PyJWT, Passlib
- **测试与 CI**：Pytest, Httpx, GitHub Actions

## 🧠 架构设计思考 (Architecture Decisions)

1. **为什么放弃数据库物理外键？**
   - 物理外键在高并发写入时会触发额外的父表行锁/间隙锁，造成性能瓶颈；且一旦未来进行分库分表，物理外键将彻底失效。本项目采用逻辑外键，在 Service 层保证数据一致性，并通过 SQLAlchemy `primaryjoin` 和 `foreign()` 完美维持 ORM 关系。
2. **为什么要重写 Pytest 测试的数据库引擎配置？**
   - 为了保证生产环境 MySQL 主键为 `BIGINT`，而测试环境 SQLite 能正常自增，在 `conftest.py` 中利用 SQLAlchemy 的反射机制动态替换了列类型，实现了测试与业务代码的完全解耦。
3. **无限极评论的软删除策略**：
   - 评论数据量相对较小，直接利用 MySQL 递归 CTE 或维护 `path` 字段较重。本项目采用一次性查出该文章的所有评论父子映射，在 Python 内存中进行广度优先搜索，最后通过一条 `UPDATE ... WHERE id IN (...)` 实现批量软删除，兼顾了性能和兼容性。

## 🚀 快速启动 (Quick Start)

### 1. 环境准备
确保本地已安装 **Python 3.13+** 与 MySQL 8.0+。

### 2. 克隆项目并安装依赖
```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
python -m venv .venv

# Windows 激活虚拟环境
.venv\Scripts\activate
# Mac/Linux 激活虚拟环境
# source .venv/bin/activate

pip install -r requirements.txt
3. 数据库配置
首先在 MySQL 中创建数据库：

sql
CREATE DATABASE myblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
复制环境变量模板：

bash
cp .env.example .env
打开 .env 文件，填入你的 MySQL 连接串和生成的 SECRET_KEY。

4. 初始化数据库 (Alembic)
bash
# 执行迁移脚本，生成所有数据表
alembic upgrade head
5. 启动服务
bash
uvicorn main:app --reload
服务启动后，访问 Swagger UI 接口文档：👉 http://127.0.0.1:8000/docs

🧪 运行自动化测试
本项目使用独立的 SQLite 内存数据库，无需配置本地 MySQL 即可运行测试：

bash
# 运行全部测试用例
pytest tests/ -v
📂 项目结构 (Project Structure)
text
myinfo/
├── app/
│   ├── core/               # 核心配置与基础组件
│   │   ├── config.py       # Pydantic 环境变量配置
│   │   ├── database.py     # 异步引擎与 Session 工厂
│   │   ├── dependencies.py # 依赖注入（JWT解析、鉴权、DB获取）
│   │   ├── models.py       # SQLAlchemy ORM 模型
│   │   └── schemas.py      # Pydantic 校验模型
│   ├── routers/            # 路由控制器
│   │   ├── admin.py        # 用户鉴权、注册、管理
│   │   └── articles.py     # 文章、评论、搜索
│   ├── utils/              # 通用工具
│   │   ├── logger.py       # 异步操作日志记录器
│   │   └── mypagination.py # 通用分页组件
│   └── main.py             # FastAPI 入口与中间件配置
├── migrations/             # Alembic 数据库迁移脚本
├── tests/                  # Pytest 自动化测试用例
├── .env.example            # 环境变量示例
├── requirements.txt        # 依赖清单
├── alembic.ini             # Alembic 配置文件
└── README.md





