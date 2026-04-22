# qq-login-adapter

独立于 `qqbot-framework` 的 QQ 登录适配器实验项目。

目标：
- 不改动现有 `qqbot-framework` 运行链路
- 单独研究 QQ 登录、事件标准化、消息发送与会话保活
- 后续可作为独立服务运行，再决定是否对接现有框架

当前阶段：
- 建立独立 HTTP 服务
- 接入 NapCat WebUI 真实登录能力
- 接入现有 OneBot 发送链路
- 实现基础事件标准化、最近消息记录、登录看门狗
- 提供一个最小 Web 面板用于观察与手工操作

## 目录说明

- `app/models.py`：内部事件/消息模型
- `app/adapter.py`：适配器接口定义 + 当前实现
- `app/session.py`：登录状态机
- `app/server.py`：独立 HTTP 服务与 API
- `app/napcat_client.py`：NapCat WebUI 客户端
- `app/onebot_client.py`：OneBot 消息发送客户端
- `app/message_store.py`：最近消息/事件快照
- `app/watchdog.py`：登录看门狗
- `app/web.py`：最小 Web 面板
- `app/main.py`：启动入口

## 当前支持的 API

### 状态与面板
- `GET /healthz`：服务健康状态
- `GET /login/state`：查看当前登录状态
- `GET /messages`：查看最近入站/出站消息与统计
- `GET /panel`：最小 Web 控制面板

### 登录与辅助
- `POST /login/qrcode`：进入扫码登录流程
- `POST /login/link`：进入链接登录流程
- `POST /login/password`：进入密码登录流程
- `POST /login/qrcode/scanned`：人工确认二维码/链接登录已完成
- `POST /login/captcha`：人工提交验证码结果
- `POST /login/new-device`：人工完成新设备确认
- `POST /login/new-device/qrcode`：获取新设备确认二维码信息
- `POST /login/new-device/poll`：轮询新设备二维码状态
- `GET /login/qrcode/export`：导出 NapCat 当前二维码文件
- `POST /login/logout`：退出当前登录态

### Watchdog
- `POST /watchdog/check`：执行一次掉线/二维码检查
- `POST /watchdog/start`：启动登录看门狗
- `POST /watchdog/stop`：停止登录看门狗
- `GET /watchdog/status`：查看登录看门狗状态

### 消息收发
- `POST /message/private`：发送私聊消息
- `POST /message/group`：发送群消息
- `POST /event`：接收入站事件并做标准化

## 事件标准化

当前已覆盖基础字段：
- `post_type`
- `message_type`
- `notice_type`
- `request_type`
- `meta_event_type`
- `sub_type`
- `user_id`
- `group_id`
- `message_id`
- `raw_message`
- `sender`
- `message`
- `received_at`
- 原始 payload 会保存在 `extra.payload`

## 当前实际能力

当前版本已经是**可运行的登录管理 + 基础消息收发服务**：
- 已支持真实读取 NapCat 登录状态
- 已支持刷新二维码、密码登录、验证码/新设备辅助
- 已支持二维码文件导出
- 已支持登录看门狗
- 已支持通过 OneBot 真实发送私聊/群聊消息
- 已支持接收入站事件并记录最近消息快照
- 已提供最小 Web 面板用于手工操作

## 仍未完成的部分

这还不是完整独立 QQ 框架，仍缺：
- 独立于 NapCat/OneBot 的底层协议 transport
- 完整业务路由/插件层
- 长期消息持久化
- 更成熟的鉴权与公网部署方案
- 更完整的自动恢复/告警机制

## 运行示例

```bash
cd /root/.openclaw/workspace/qq-login-adapter
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9011
```

访问：
- `http://127.0.0.1:9011/healthz`
- `http://127.0.0.1:9011/panel`

## 结论

它现在已经不再只是“登录壳子”，而是：

**NapCat 登录中控 + OneBot 基础消息收发 + 最近事件观察面板**

如果后续继续推进，比较合理的方向是：
1. 补消息路由/handler 层
2. 补持久化存储
3. 做更完整的认证 Web 面板
4. 再决定要不要继续走真正独立 transport
