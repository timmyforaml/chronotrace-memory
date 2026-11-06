# v0.23 安装与运行指南

本指南用于新建独立实例，不自动更新正式服务。需要 Python 3.12。请求字段见 [API](../../docs/API.md)，配置、容量及数据用途见[部署说明](../../docs/DEPLOYMENT.md)。

## 1. 准备源码

从仓库根目录执行：

```bash
cd online/v0.23-contract03
python3.12 prepare_source.py --output source
python3.12 -m venv .venv
.venv/bin/python -m pip install -r source/requirements.txt
```

Windows PowerShell：

```powershell
cd online/v0.23-contract03
py -3.12 prepare_source.py --output source
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r source\requirements.txt
```

脚本校验原压缩包 SHA256、复制已记录长度修复、逐字节核验 42 文件并生成真实 manifest，源码身份为 `4f7aa733e817f906605e6c9ef88c6a5f9e39ef54e5acaa2283e1f6ac997d8429`。输出目录存在则拒绝覆盖。只核对原始快照时用 `--archive-only --output source-original`。不要改变行尾后再校验。准备过程不访问服务器、不调用模型、不提交评测。

## 2. 配置环境

在 Git 之外私密设置 `MEMORY_API_KEY`、`DASHSCOPE_API_KEY`，不要把真实值写入仓库、命令参数或公开日志。前者用于本服务鉴权，后者用于 embedding 供应方；平台 Eval Key 不属于服务启动配置。

Linux Bash 非敏感设置如下，数据库路径先换成实例独占绝对路径：

```bash
export AE_EMBEDDING_BACKEND=dashscope
export AE_EMBEDDING_URL=https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding
export AE_EMBEDDING_DIMENSIONS=1024
export AE_EMBEDDING_BATCH_SIZE=10
export AE_EMBEDDING_TIMEOUT=60
export AE_EMBEDDING_MAX_ATTEMPTS=3
export AE_EMBEDDING_MAX_REQUESTS=0
export AE_MODE=query_document_evidence
export AE_CONTEXT_CHARS=24000
export AE_DATABASE=/ABSOLUTE/INSTANCE/PATH/memory.sqlite3
```

PowerShell：

```powershell
$env:AE_EMBEDDING_BACKEND = 'dashscope'
$env:AE_EMBEDDING_URL = 'https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding'
$env:AE_EMBEDDING_DIMENSIONS = '1024'
$env:AE_EMBEDDING_BATCH_SIZE = '10'
$env:AE_EMBEDDING_TIMEOUT = '60'
$env:AE_EMBEDDING_MAX_ATTEMPTS = '3'
$env:AE_EMBEDDING_MAX_REQUESTS = '0'
$env:AE_MODE = 'query_document_evidence'
$env:AE_CONTEXT_CHARS = '24000'
$env:AE_DATABASE = 'D:\CHOOSE-PRIVATE-INSTANCE\memory.sqlite3'
```

供应方 endpoint 必须与部署区域和配置一致，完整指定 HTTPS URL，不含凭据；模型固定为 `text-embedding-v4`。`AE_EMBEDDING_MAX_REQUESTS=0` 表示进程不额外设请求数上限，供应方配额仍需保障。默认超时 60 秒、瞬态错误最多 3 次尝试；明确长度错误才使用已记录修复。正式启动前清除继承的 `AE_LOCAL_NO_AUTH` 绕过设置。

## 3. 启动

在还原的 source 目录运行一个 worker：

```bash
cd source
../.venv/bin/python -m uvicorn adaptive_evidence.chronotrace_api:app \
  --host 127.0.0.1 --port 18406 --workers 1 --no-access-log
```

Windows：

```powershell
cd source
..\.venv\Scripts\python.exe -m uvicorn adaptive_evidence.chronotrace_api:app --host 127.0.0.1 --port 18406 --workers 1 --no-access-log
```

另一个终端执行 `curl http://127.0.0.1:18406/health`，应返回 HTTP 200 和真实源码身份。Health 不证明供应方配额、实际向量调用或 Full 完成状态。

正式部署通过公开 HTTPS 代理映射 Add/Search/Health，可加已登记前缀。正式 m04 后端为 18104；本指南的 18406 用于独立本地实例，不指向活动评测数据库。服务管理器使用专用环境、绝对源码路径和私密配置。代理保持正文、JSON 和错误码，容纳同步长请求，不能提前返回成功或改为后台收据。

## 4. 合成验收

安装依赖后，在本在线目录运行 13 项契约测试：

```bash
.venv/bin/python -m unittest discover -s . -p test_five_requirements.py -v
```

在 source 目录运行包内 64 项回归：

```bash
../.venv/bin/python -m unittest discover -s tests -v
```

Windows 替换为对应 `.venv\Scripts\python.exe` 路径。测试使用虚构内容和确定性编码器或 HTTP mock，不调用真实模型。覆盖隔离、跨会话、持久化后可见、16 路重试幂等、冲突、重开库、有序数组、响应界限、鉴权和失败边界；不代表官方准确率或状态抽取收益。

## 5. 数据与维护

主库后缀分别生成 `.envelopes.sqlite3` 与 `.chronotrace.sqlite3`，整组文件应一致备份、核验和恢复。保持原文不可变与实例数据隔离，不换模型重建向量。

Full 原配置为 Add 并发 16、Search 并发 16、`top_k=100`。受理后保持接口、代码、模型及评测参数稳定；按脱敏错误和官方回执排查，恢复遵守平台允许的原任务检查点机制。赛事数据及派生副本在任务完成后 30 天内清理，除非另获书面许可。

完整一段式文字见[提交说明](../../docs/COMMIT_AND_RUN_GUIDE.md)。根目录 `pip install .` 只安装离线 v0.1.1，不能替代此在线安装流程。
