# ChronoTrace Memory · 时序溯源记忆

Source-grounded bitemporal state memory, with immutable source snapshots and a separate append-only derived ledger.

**ChronoTrace Memory** 是一个状态记忆研究原型：用实体、窄属性、限定词识别同一属性，分别追踪有效时间（事情何时成立）与记录时间（系统何时知道），区分真实状态变更和对旧记录的显式更正，并保留原文证据与更正历史。

这是可独立运行的 Python 状态内核与结构化快照查询工具。**当前版本需要显式标注的事件，不包含已验证有效的自动自然语言记忆抽取器。** 运行不需要 GPU、模型、API Key 或网络连接；Python 3.10+，运行时仅用标准库。

## 快速运行

在克隆的仓库目录中执行：

```powershell
git clone https://github.com/timmyforaml/chronotrace-memory.git
cd chronotrace-memory
python -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python examples/demo.py
.venv\Scripts\python -m unittest discover -s tests -v
```

Linux/macOS 将 `.venv\Scripts\python` 替换为 `.venv/bin/python`。安装过程可能从 PyPI 下载构建工具；程序本身没有第三方运行依赖。源码免安装方式见[完整运行指南](docs/USER_GUIDE.md)。

## 同一段历史，不同时间语义

一月记录 Alice 住在 Paris；四月她搬到 Berlin；五月明确更正“一月应为 Lyon，Paris 是错误记录”。

| 查询 | 结果 | 来源 |
|---|---|---|
| 八月的当前住地 | Berlin | s2 |
| 二月住地，使用后来收到的更正 | Lyon | s3，指向 s1 |
| 截至三月已知的二月住地 | Paris | s1 |
| 完整住地断言与更正历史 | Paris → Berlin；更正为 Lyon | s1、s2、s3 |

```powershell
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent current --as-of 2026-08-01
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent past --as-of 2026-02-01
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent past --as-of 2026-02-01 --known-at 2026-03-01
```

只需查看 JSON 输出的 `answer_values` 即可看到 Berlin、Lyon、Paris。`evidence` 保留原文和来源偏移，`relations` 给出更正关系；更正句可能作为来源证据附带返回，不代表它是当前值。

## 机制边界

- 原文快照只读；断言、关系、投影可写入另一个 SQLite 文件。派生表有禁止更新/删除的触发器。
- 显式更正必须精确指向同一属性中唯一的更早原句；无独立有效时间的更正继承目标区间。
- 实体、属性、限定词使用显式标识；共享关键词不会使两个属性自动合并。属性语义标注仍由调用方负责。
- 无法确定先后、多值属性、未解析更正目标保留不确定性。来源时间缺失时，无法证明该事实在指定时间已成立或已知。
- 本工具每次查询接收完整相关快照；SQLite 是派生审计存储，不会自动补齐本次未提供的历史，也不提供通用用户画像、图选材或程序记忆。

## 已知研究结果

冻结本地 development 288 对评分全部有效：exact 官方 0.32.0 基线与研究候选的六数据集宏平均均为 **42.36%**，逐题收益 **0**、回退 **0**，最终输入变化 **0**。自动抽取链路未激活状态投影；holdout 未运行。没有 Smoke/Full 提交或晋升。

这说明本次自动集成没有取得收益，不能把内核测试或本仓库的结构化示例当作基准提升。发布用 CLI 适配层是在冻结评测之后新增的工程接口，没有重新计入上述分数。详见[研究结果](docs/RESEARCH_RESULTS.md)和[来源与版本审计](docs/PROVENANCE.md)。

Mem0 固定开源源码仅作为更新历史机制参考；没有将其托管平台成绩归给开源 SDK 或本项目。仓库未包含评测题目、原始对话、参考答案、模型权重、私有数据库或认证信息。

MIT License。变更内容见 [CHANGELOG.md](CHANGELOG.md)。
