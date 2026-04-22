# qq-login-adapter

独立于 `qqbot-framework` 的 QQ 登录适配器实验项目。

目标：
- 不改动现有 `qqbot-framework` 运行链路
- 单独研究 QQ 登录、事件标准化、消息发送与会话保活
- 后续可作为独立服务运行，再决定是否对接现有框架

当前阶段：
- 建立独立 HTTP 服务骨架
- 定义内部事件模型
- 实现登录状态机与人工辅助接口骨架
- 预留底层 QQ transport 接入点

## 目录说明

- `app/models.py`：内部事件/消息模型
- `app/adapter.py`：适配器接口定义 + 当前占位实现
- `app/session.py`：登录状态机
- `app/server.py`：独立 HTTP 服务与登录 API
- `app/main.py`：启动入口

## 当前支持的登录 API（状态机骨架）

- `GET /healthz`：服务健康状态
- `GET /login/state`：查看当前登录状态
- `POST /login/qrcode`：进入扫码登录流程
- `POST /login/link`：进入链接登录流程
- `POST /login/password`：进入密码登录流程
- `POST /login/qrcode/scanned`：人工确认二维码/链接登录已完成
- `POST /login/captcha`：人工提交验证码结果
- `POST /login/new-device`：人工完成新设备确认
- `POST /login/new-device/qrcode`：获取新设备确认二维码信息
- `POST /login/new-device/poll`：轮询新设备二维码状态
- `GET /login/qrcode/export`：导出 NapCat 当前二维码文件
- `POST /watchdog/check`：执行一次掉线/二维码检查
- `POST /watchdog/start`：启动登录看门狗
- `POST /watchdog/stop`：停止登录看门狗
- `GET /watchdog/status`：查看登录看门狗状态
- `POST /login/logout`：退出当前登录态

## 说明

当前版本实现的是**真实可运行的登录状态管理 API**，并且已经接入 **NapCat WebUI 的真实登录接口**。
也就是说：
- 登录阶段切换、人工辅助流程、状态查询已经可运行
- 已支持真实读取 NapCat 登录状态、刷新二维码、发起密码登录、验证码/新设备辅助
- 已支持二维码文件导出，以及登录看门狗的单次检查/后台轮询
- 真正的独立 QQ 协议层、消息收发仍待后续接入

下一步可以继续增强二维码导出、告警通知、自动恢复策略，或在 `PlaceholderQQLoginAdapter` 下替换成更独立的 transport 实现。
