# qq-login-adapter

独立于 `qqbot-framework` 的 QQ 登录适配器实验项目。

目标：
- 不改动现有 `qqbot-framework` 运行链路
- 单独研究 QQ 登录、事件标准化、消息发送与会话保活
- 后续可作为独立服务运行，再决定是否对接现有框架

当前阶段：
- 建立最小项目骨架
- 定义内部事件模型
- 预留适配器接口与登录会话管理入口

## 目录说明

- `app/models.py`：内部事件/消息模型
- `app/adapter.py`：适配器接口定义
- `app/session.py`：登录会话与保活状态骨架
- `app/server.py`：独立 HTTP 服务骨架
- `app/main.py`：启动入口

## 说明

这个项目目前只是独立骨架，不接管现有机器人，不影响当前 NapCat + OneBot 运行。
