# v0.23 Add / Search 接口

以下均为虚构示例，路径是服务内部路由，公网可增加已登记前缀。依据 2026-11-04 核对的 [API Guide](https://agentmemories.ai/api-guide)、[Documentation](https://agentmemories.ai/docs)，结合发布源码的实际字段校验说明。

## 鉴权和 Health

Add/Search 任选一种鉴权请求头：

```http
Authorization: Bearer <MEMORY_SYSTEM_KEY>
Authorization: Token <MEMORY_SYSTEM_KEY>
X-Api-Key: <MEMORY_SYSTEM_KEY>
```

服务通过 `MEMORY_API_KEY` 配置此密钥，与平台 Eval Key 分开。正式实例保持鉴权启用。`GET /health` 无需鉴权，成功返回 HTTP 200，JSON 包含版本、`source_manifest_sha256`、模型、模式和预算。核验源码还需校验实际文件，不能只信目录名或 Health 字段。

## POST /add

```json
{
  "request_id": "demo-write-001",
  "user_id": "demo-user-alice",
  "session_id": "demo-session-january",
  "messages": [
    {
      "role": "user",
      "timestamp": 1767225600000,
      "content": "Alice lives in Paris."
    }
  ]
}
```

| 字段 | 约束 |
|---|---|
| `request_id` | 必填非空字符串；同一用户的同一逻辑请求重试时复用 |
| `user_id` | 必填非空字符串；Search 必须使用完全相同的隔离标识 |
| `session_id` | 必填非空字符串；标识来源会话，不限制后续跨会话检索 |
| `messages` | 必填非空有序数组；每条含非空 `role` 和 `content` |
| `messages[].timestamp` | 可选 Unix 毫秒整数或 null；不接受布尔值和时间字符串 |
| `messages[].content` | 非空文本字符串，或只含 text 部件的非空有序数组 |

有序文本数组示例：

```json
[
  {"type": "text", "text": "First source paragraph."},
  {"type": "text", "text": "Second source paragraph."}
]
```

原始数组独立保存，检索文本按顺序以 LF 连接；普通字符串保持原文。此版不支持 `image_url`，不声明多模态接入。图片、空白内容、未声明额外字段返回 422。

同步持久化且立即可检索后，HTTP 200 响应：

```json
{
  "success": true,
  "request_id": "demo-write-001",
  "user_id": "demo-user-alice",
  "session_id": "demo-session-january"
}
```

幂等边界为 `(user_id, request_id)`。相同请求不重复写入；同一身份但修改会话、消息或原始内容形式返回 409。中断后相同请求重试可补齐未完成的派生或完成回执；失败不返回虚假成功。

## POST /search

```json
{
  "user_id": "demo-user-alice",
  "query": "Where does Alice live?",
  "top_k": 5
}
```

| 字段 | 约束 |
|---|---|
| `user_id` | 必填非空字符串；只检索该用户的记忆 |
| `query` | 必填非空字符串，或有序 text 内容数组 |
| `top_k` | 必填整数，1–100；正式 Full 为 100 |
| `options` | 可选字符串数组，仅用于题目给定的检索上下文，不作为答案或记忆写入 |

Search 不接受 `session_id`、`filters`、`metadata`、`answer`、`gold` 等额外字段。条目按证据优先顺序返回，数量可以少于 `top_k`。

最小响应结构如下；真实 ID 由存储产生，内容可带角色、时间与派生注记：

```json
{
  "data": [
    {"id": "demo-memory-id", "content": "[user] Alice lives in Paris."}
  ]
}
```

`id`、`content` 都是非空字符串；可附带 `score`、`created_at` 等字段，调用方以返回顺序为准。无可返回记忆时：

```json
{"data": []}
```

接口只返回来源记忆证据，不生成当前问题的最终答案，不返回选项字母，不读取外部金标。最终回答及评分由平台执行。

## 错误与重试

| HTTP | 含义与处理 |
|---|---|
| 401 | 鉴权缺失或错误；检查密钥配置 |
| 409 | 相同请求身份的正文冲突；不得覆盖原请求 |
| 422 | 字段、类型或内容不符合 Textual 契约；不回显请求正文 |
| 503 | embedding 上游等可用性错误；附 `Retry-After: 5`，仍需按原因排查 |
| 其他 5xx / 网络故障 | 保留脱敏状态与时间，排查服务及供应方；不能视为写入成功 |

并非所有 HTTP 400 都是瞬态故障。已记录的长度修复只识别供应方明确的输入长度错误，用同一模型对完整文本分段后加权合并向量；其他错误继续失败。普通成功输入沿原路径处理，超长输入向量表示会改变。版本身份见[发布记录](PROVENANCE.md)。
