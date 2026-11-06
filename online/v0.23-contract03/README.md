# ChronoTrace Memory v0.23 · Textual 在线服务

版本 v0.23，修订 `source-local-extents-01.contract03`，入口 `adaptive_evidence.chronotrace_api:app`。参赛者已提交 Full，最终成绩及公榜状态以平台为准。此服务与根目录 v0.1.1 离线结构化状态内核分别发布。

## 文件与版本

| 文件 | 用途 |
|---|---|
| `source.tar.gz`、`manifest.json`、`package.json` | 2026-10-31 原始固定快照，保留原字节及打包时状态 |
| `recorded-length-repair/remote_encoder.py` | 后续已记录并获用户授权的长度恢复精确副本 |
| `recorded-length-repair/manifest.json` | 修复后 42 个服务文件 SHA256 清单 |
| `prepare_source.py` | 仅使用标准库还原及校验文件，生成真实 manifest |
| `test_five_requirements.py` | 13 项合成契约验收，不调用网络模型 |

本目录已提供完整服务复现材料，包含线上使用的运行兼容性修复，核心方法和接口保持 v0.23 一致。发布快照清单为 `027b67c8fcb8…`，默认还原代码清单为 `4f7aa733e817…`，完整哈希见[版本记录](../../docs/PROVENANCE.md)。原包 `Full_submitted: false` 是打包时字段，不表示当前提交状态。

## 还原与运行

使用 Python 3.12，在本目录执行：

```bash
python3.12 prepare_source.py --output source
python3.12 -m venv .venv
.venv/bin/python -m pip install -r source/requirements.txt
```

脚本默认准备包含运行兼容性修复的完整服务代码，拒绝覆盖已有输出目录。如需核对历史发布快照，可使用 `python3.12 prepare_source.py --archive-only --output source-original`。随后按[完整指南](RUN_GUIDE.zh-CN.md)配置私密环境、启动服务、设置 HTTPS 代理并验收。

## 行为与限制

`user_id` 严格隔离，同用户跨会话可查；同步 Add 在持久化及可检索写入后返回 200，以 `(user_id, request_id)` 幂等。Search 返回按优先顺序排列、不超过 `top_k` 的 `data` 证据数组。有序 text 数组原样保存，检索时以 LF 连接；图片不支持。字段与错误见 [API](../../docs/API.md)。

线上使用 `text-embedding-v4`，无生成式 LLM，Answer/Eval 由平台完成。状态解析窄且局限于单条来源，不保证全局最新事实或通用自动更正解析。长度修复前 contract03 Smoke 为 46/46、61.0243，窗口内状态 frame 和 query projection 均为 0；不代表已证明状态收益，也不是修复后 Full 分数。

密钥、数据库、评测数据和模型不发布。源码自带许可证及版权声明保留，数据处理要求见[部署说明](../../docs/DEPLOYMENT.md)。
