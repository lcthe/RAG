# 智云开放平台 API 文档

> Base URL: https://api.zhiyun-tech.com/v2
> 认证方式：Bearer Token（OAuth 2.0）
> 文档版本：v2.3 | 最后更新：2025年4月

## 认证

所有 API 请求需要在 Header 中携带 Token：

`
Authorization: Bearer <your_access_token>
`

获取 Token 流程：
1. 调用 POST /auth/token 获取 access_token（有效期 2 小时）
2. 使用 refresh_token 刷新（有效期 30 天）

`
POST /auth/token
Content-Type: application/json

{
  "app_id": "your_app_id",
  "app_secret": "your_app_secret",
  "grant_type": "client_credentials"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
`

## 设备管理

### 获取设备列表

`
GET /devices
Query: page=1&page_size=20&room_id=living_room

Response:
{
  "total": 15,
  "devices": [
    {
      "device_id": "ZY-SP100-ABC123",
      "name": "客厅音箱",
      "type": "speaker",
      "model": "ZY-SP100",
      "online": true,
      "room": "living_room",
      "firmware_version": "2.1.3",
      "last_online": "2025-04-20T10:30:00Z",
      "properties": {
        "volume": 60,
        "playing": false,
        "current_music": null
      }
    }
  ]
}
`

### 控制设备

`
POST /devices/{device_id}/command
Content-Type: application/json

{
  "command": "set_property",
  "params": {
    "property": "volume",
    "value": 80
  }
}

Response:
{
  "status": "success",
  "request_id": "req_abc123",
  "timestamp": "2025-04-20T10:35:00Z"
}
`

### 批量控制

`
POST /devices/batch_command
Content-Type: application/json

{
  "device_ids": ["ZY-LT100-001", "ZY-LT100-002", "ZY-LT100-003"],
  "command": "set_property",
  "params": {
    "property": "brightness",
    "value": 50
  }
}
`

## 场景管理

### 创建场景

`
POST /scenes
Content-Type: application/json

{
  "name": "回家模式",
  "description": "检测到回家时自动开启",
  "triggers": [
    {
      "type": "location",
      "params": {
        "user_id": "user_001",
        "enter_area": {
          "lat": 31.2304,
          "lng": 121.4737,
          "radius": 500
        }
      }
    }
  ],
  "actions": [
    {
      "device_id": "ZY-LT100-001",
      "command": "set_property",
      "params": { "power": "on", "brightness": 80 }
    },
    {
      "device_id": "ZY-AC100-001",
      "command": "set_property",
      "params": { "power": "on", "temperature": 26, "mode": "cool" }
    }
  ],
  "enabled": true
}
`

### 执行场景

`
POST /scenes/{scene_id}/execute

Response:
{
  "status": "executed",
  "scene_id": "scene_abc123",
  "execution_time_ms": 320,
  "action_results": [
    { "device_id": "ZY-LT100-001", "status": "success" },
    { "device_id": "ZY-AC100-001", "status": "success" }
  ]
}
`

## 语音接口

### 语音识别（ASR）

`
POST /voice/asr
Content-Type: multipart/form-data

音频文件参数：
- audio: 音频文件（WAV/MP3，最大 10MB）
- language: "zh-CN" | "en-US"
- format: "pcm" | "wav" | "mp3"

Response:
{
  "text": "打开客厅的灯",
  "confidence": 0.96,
  "language": "zh-CN",
  "duration_ms": 2300
}
`

### 语义理解（NLU）

`
POST /voice/nlu
Content-Type: application/json

{
  "text": "把客厅灯调到50%亮度",
  "context": {
    "user_id": "user_001",
    "current_room": "living_room"
  }
}

Response:
{
  "intent": "device.control",
  "confidence": 0.98,
  "slots": {
    "device_type": "light",
    "room": "living_room",
    "property": "brightness",
    "value": 50,
    "unit": "percent"
  }
}
`

### 对话管理（LLM）

`
POST /voice/chat
Content-Type: application/json

{
  "message": "明天上海天气怎么样？如果下雨的话提醒我带伞",
  "session_id": "sess_abc123",
  "user_id": "user_001"
}

Response:
{
  "reply": "明天上海多云转小雨，气温 18-24°C，降水概率 70%。建议您带伞出门哦！",
  "session_id": "sess_abc123",
  "tool_calls": [
    {
      "tool": "weather_query",
      "params": { "city": "上海", "date": "2025-04-21" }
    },
    {
      "tool": "reminder_set",
      "params": { "time": "2025-04-21T07:00:00", "message": "今天有雨，记得带伞" }
    }
  ]
}
`

## 数据查询

### 设备历史数据

`
GET /devices/{device_id}/history
Query: property=temperature&start=2025-04-01&end=2025-04-20&interval=1h

Response:
{
  "device_id": "ZY-TH100-001",
  "property": "temperature",
  "data_points": [
    { "timestamp": "2025-04-01T00:00:00Z", "value": 22.5 },
    { "timestamp": "2025-04-01T01:00:00Z", "value": 22.3 },
    ...
  ]
}
`

## 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求体格式和必填字段 |
| 401 | Token 无效或过期 | 重新获取 Token |
| 403 | 无权限访问该设备 | 确认设备已绑定到当前账号 |
| 404 | 设备/场景不存在 | 检查 device_id 或 scene_id |
| 429 | 请求过于频繁 | 降低请求频率，等待 60 秒后重试 |
| 500 | 服务器内部错误 | 稍后重试，如持续失败请联系技术支持 |
| 1001 | 设备离线 | 确认设备已通电且网络正常 |
| 1002 | 指令执行超时 | 设备可能响应缓慢，建议重试 |
| 1003 | 不支持的指令 | 检查设备类型是否支持该命令 |

## SDK 与示例

### Python SDK

`python
from zhiyun_sdk import ZhiyunClient

client = ZhiyunClient(
    app_id="your_app_id",
    app_secret="your_app_secret"
)

# 获取设备列表
devices = client.devices.list(room="living_room")

# 控制设备
client.devices.command(
    device_id="ZY-LT100-001",
    command="set_property",
    params={"brightness": 80}
)

# 创建场景
scene = client.scenes.create(
    name="回家模式",
    triggers=[{"type": "location", "enter_area": {"lat": 31.23, "lng": 121.47, "radius": 500}}],
    actions=[
        {"device_id": "ZY-LT100-001", "command": "set_property", "params": {"power": "on"}}
    ]
)
`

### 安装

`ash
pip install zhiyun-sdk
`

## 技术支持

- 开发者社区：https://developer.zhiyun-tech.com/community
- 工单系统：https://developer.zhiyun-tech.com/ticket
- 技术邮箱：dev-support@zhiyun-tech.com
