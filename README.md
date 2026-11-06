# ChronoTrace Memory · 时序溯源记忆

状态内核开发、生命周期契约和合成演示的入口见[内核工作流](handbook/ENGINE_WORKFLOW.md)。

**ChronoTrace Memory v0.23** 是面向 Agent Memory Challenge 文本赛道的记忆服务，提供同步 Add、按用户隔离的 Search、不可变原文存储和独立的状态派生历史。参赛系统返回记忆证据，平台统一生成最终回答并评分。

本页以 v0.23 在线服务为主。仓库同时保留 [v0.1.1 离线状态内核](handbook/USER_GUIDE.md)，用于演示有效时间、记录时间和显式更正；两者的入口、依赖及评测记录分别说明。

## 参评版本与材料

| 项目 | 说明 |
|---|---|
| 系统 / 参评版本 | ChronoTrace Memory / v0.23 |
| 赛道 | Textual；不声明 Coding 或 Multimodal 支持 |
| 在线修订 | `source-local-extents-01.contract03` |
| 服务入口 | `adaptive_evidence.chronotrace_api:app` |
| 接口 | `POST /add`、`POST /search`、`GET /health`；公网代理可以配置路径前缀 |
| 模型 | Add/Search 使用 `text-embedding-v4`，1024 维；服务内无生成式 LLM |
| 已提交 Full 配置 | Add 并发 16、Search 并发 16、`top_k=100` |
| 提交状态 | 参赛者已提交 Full；最终成绩及公榜状态以平台审核记录为准 |

公开仓库已包含 v0.23 的源码、运行兼容性修复和完整复现工具，线上部署与公开实现采用相同的核心方法和接口。按下方指南可直接准备完整服务代码；文件校验信息见[版本与发布记录](handbook/PROVENANCE.md)。

- [在线服务与源码准备](online/v0.23-contract03/README.md)
- [完整安装与运行指南](online/v0.23-contract03/RUN_GUIDE.zh-CN.md)
- [Add/Search 字段、示例和错误处理](handbook/API.md)
- [部署容量、数据处理及运维约束](handbook/DEPLOYMENT.md)
- [提交说明与一段式运行指南](handbook/COMMIT_AND_RUN_GUIDE.md)

## 服务如何工作

Add 校验请求身份与消息顺序，保存原始请求 envelope，完成原文、分块和向量持久化，再记录派生历史和完成回执。Search 只在同一 `user_id` 下检索，组织带来源的原文证据，并在满足窄语法和时间条件时附加可追溯的状态注记。

原文保存在主库；原始有序内容数组保存在独立 envelope 库；断言及查询投影保存在另一派生库。更正或版本解释不覆盖原文。同一用户可跨 `session_id` 检索，`session_id` 仅用于组织来源。

| 接入要求 | 本服务行为 |
|---|---|
| 严格隔离 | `user_id` 是检索边界；不同用户即使复用 `request_id` 也独立处理 |
| 写后可见 | 同步 Add 完成持久化及可检索写入后才返回 HTTP 200 |
| 请求幂等 | 按 `(user_id, request_id)` 识别逻辑请求；相同重试不重复写入，冲突返回 409 |
| 标准响应 | Search 返回 `{"data": [...]}`，空结果为 `{"data": []}`；保留证据顺序且不超过 `top_k` |
| 返回证据 | 返回已写入的记忆及来源注记；最终回答、选项判断与代码任务由平台执行 |

## 快速启动在线服务

使用 Python 3.12。下面在新目录中还原已记录的 Full 服务源码；准备过程不部署、不提交评测，也不调用模型。

```bash
git clone https://github.com/timmyforaml/chronotrace-memory.git
cd chronotrace-memory/online/v0.23-contract03
python3.12 prepare_source.py --output source
python3.12 -m venv .venv
.venv/bin/python -m pip install -r source/requirements.txt
```

在 Git 之外配置私密环境变量 `MEMORY_API_KEY`、`DASHSCOPE_API_KEY`，以及完整的 `AE_EMBEDDING_URL`。按[运行指南](online/v0.23-contract03/RUN_GUIDE.zh-CN.md)设置检索模式、维度、预算和实例独占数据库后，从 `source` 目录启动：

```bash
../.venv/bin/python -m uvicorn adaptive_evidence.chronotrace_api:app \
  --host 127.0.0.1 --port 18406 --workers 1 --no-access-log
```

Windows 对应命令和离线验收见运行指南。`18406` 是独立本地实例的示例端口。

## 状态与历史的适用范围

v0.23 在线解析器使用来源内的实体、窄属性和明确时间表达，不因共享关键词就建立跨消息属性关系；不能解析或不能证明时间关系时保留原文检索路径。它不具备通用自然语言状态抽取、任意跨来源更正解析或完整用户画像能力。一次原文中的“current”也不能证明它是用户全部历史中的全局最新状态。

离线 v0.1.1 接受显式结构化事件，可演示双时间查询：

| 同一组合成历史中的查询 | 返回值 | 来源 |
|---|---|---|
| 八月当前住地 | Berlin | s2 |
| 二月住地，应用后来收到的更正 | Lyon | s3，指向 s1 |
| 截至三月已知的二月住地 | Paris | s1 |

CLI、合成数据和派生账本用法见[离线指南](handbook/USER_GUIDE.md)。该示例不代表在线系统已经验证出自动状态推理收益。

## 验证与成绩

| 记录 | 结果与边界 |
|---|---|
| contract03 官方 Smoke | 46/46，61.0243；属于长度修复前的 contract03，不是 Full 成绩 |
| 在线契约验收 | 13 项合成测试，覆盖隔离、同步提交、幂等、文本数组、证据响应及鉴权 |
| 服务回归 | 原压缩包附带 64 项回归测试，与成绩评测分开 |
| 早期离线研究 | 固定 development 288 对有效评分，六数据集宏平均两臂均 42.36%，收益/回退 0/0；holdout 未运行 |
| 状态机制收益 | 既有记录未证明最终答案增益；该次 contract03 Smoke 窗口内状态 frame 和 query projection 均为 0 |
| Full | 已提交；不发布未经核验的 Full 分数，提交不等同于公榜通过 |

研究记录见[冻结本地研究结果](handbook/RESEARCH_RESULTS.md)。运行检查不能替代完整的官方评分。

## 数据与许可证

公开仓库不分发赛事题目、原始评测对话、参考答案、模型权重、数据库或凭据。赛事数据仅用于当前评测；任务完成后按官方要求在 30 天内删除相关数据，除非另获书面保留许可。原文不可变指运行期间不覆盖内容，整套评测数据的授权清理仍须执行。

许可证见 [LICENSE](LICENSE)，源码压缩包内随附的许可证及版权声明保留原样。变更见 [CHANGELOG.md](CHANGELOG.md)。赛事要求以 [API Guide](https://agentmemories.ai/api-guide) 与 [Documentation](https://agentmemories.ai/docs) 为准；本次文档核对日期为 2026-11-04。
