# 完整运行指南

## 1. 环境与安装

要求 Python 3.10+。仓库地址：[timmyforaml/chronotrace-memory](https://github.com/timmyforaml/chronotrace-memory)。

Windows PowerShell：

```powershell
git clone https://github.com/timmyforaml/chronotrace-memory.git
cd chronotrace-memory
python -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python examples/demo.py
.venv\Scripts\python -m unittest discover -s tests -v
```

Linux/macOS：

```bash
git clone https://github.com/timmyforaml/chronotrace-memory.git
cd chronotrace-memory
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python examples/demo.py
.venv/bin/python -m unittest discover -s tests -v
```

安装只需 setuptools 构建工具；运行时零第三方依赖。安装到虚拟环境后无需激活，直接使用上述完整解释器路径即可。

若环境无法下载构建工具，也可从源码直接运行。Windows：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python examples/demo.py
python -m unittest discover -s tests -v
python -m chronotrace_memory --input examples/alice.json --intent current --as-of 2026-08-01 --entity Alice --attribute home_city
```

Linux/macOS 对应使用 `PYTHONPATH=src python3 examples/demo.py` 等命令。

## 2. 当前、历史及当时已知

在仓库目录运行，Windows 使用 `.venv\Scripts\python`，其他系统使用 `.venv/bin/python`：

```powershell
# 当前状态，明确指定有效时间参考点：Berlin
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent current --as-of 2026-08-01

# 历史状态，使用所有已提供的事后更正：Lyon
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent past --as-of 2026-02-01

# 历史状态，同时限制当时已记录的知识：Paris
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent past --as-of 2026-02-01 --known-at 2026-03-01

# 完整历史，包括错误记录及更正关系
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent history

# 单独保存派生审计，不改原始JSON
.venv\Scripts\python -m chronotrace_memory --input examples/alice.json --entity Alice --attribute home_city --intent current --as-of 2026-08-01 --ledger data/derived.sqlite3 --scope alice-demo
```

`current` 未提供 `--as-of` 时使用当前 UTC 时间。`past` 不提供 `--as-of` 时尝试返回唯一最新状态之前的状态；仅有一条记录不能证明更早状态。`history` 不接受 `--as-of`，可使用 `--known-at` 查看截至某记录时间可见的历史。未指定 `--known-at` 时允许使用本次快照中的全部记录时间。

输入时间支持 ISO-8601，未标时区按 UTC 解释；例如 `2026-03-01` 表示该日 UTC 零点，包含整天需用合适的日终时间戳。Python API 也接受 Unix 毫秒。来源中的 `valid_from`、`valid_to` 仅接受原句里出现的 `YYYY-MM-DD` 字面量；有效区间为左闭右开。

## 3. 使用自己的快照

从 `examples/alice.json` 复制并修改，保留 `sources` 与 `events` 两个数组。该文件的全部内容均为合成材料。

`sources` 每项：

| 字段 | 含义 |
|---|---|
| source_id | 快照内唯一的来源标识，不作为时间排序依据 |
| body | 不可变原文 |
| role | 只有 user 原文可生成状态断言 |
| speaker | 可选的说话人标识，用于验证属性归属 |
| recorded_at | 系统收到该原文的时间；缺失时无法确定其记录时间 |
| start | 可选，body 在完整来源里的字符偏移，默认0 |
| request_id / session_id / position | 可选的原始顺序元数据；未知值不要编造 |

`events` 每项必须包含：

| 字段 | 含义 |
|---|---|
| source | 对应 sources 的零起始下标 |
| entity | 实体名或 @speaker，必须有原文/说话人锚定 |
| attribute | 窄属性标识，如 home_city；调用方负责同义属性归一化 |
| qualifier | 进一步限定属性，无限定时空字符串 |
| value / quote | 值及逐字原句；value 必须出现在 quote，quote 必须出现在原文 |
| kind | ASSERT、CORRECT 或 RETRACT |
| target_quote | 更正/撤回的精确旧句；普通断言为空字符串 |
| valid_from / valid_to | 原句里的 ISO 日期；缺失用空字符串，不从记录时间虚构起始日期 |
| cardinality | single 或 multi |
| past_only | true 表示明确只描述过去，否则 false |

显式更正验证目前只识别英文的 correction、wrong、actually 等标记。中文原文可以保留和输出，但中文更正提示、自然语言日期及自动属性归一化尚无可靠支持。不能仅把事件类型改成 CORRECT 就绕过原文锚定。

输入 JSON 不会被修改。可选 SQLite 账本中只存派生断言、关系、查询投影及其来源信息；派生记录可能包含原文片段，因此默认被 `.gitignore` 排除。每次查询仍需提供完整相关快照；仅提供增量事件不会自动加载旧断言。多用户系统应由调用方隔离快照与存储，本原型没有认证或服务接口。

## 4. 理解输出

`answer_values` 是确定选中的状态值；`resolution` 为 resolved、ambiguous、no_matching_state 或 history。不能把空数组解释为事实不存在：它也可能表示缺少时间证据或没有符合条件的状态。`evidence` 是选中原文及更正来源，`statuses` 区分当前/历史选中、旧记录被更正和未解决冲突；不要把全部 evidence 的值直接当作答案。`rejected` 显式列出未通过来源验证的事件与原因。

`raw_sources_unchanged` 与 `source_digest` 用于核对输入未变；这是审计辅助，不是外部签名或防篡改保证。数据库禁止通过普通 UPDATE/DELETE 更改派生行，但有文件权限的人仍可删除数据库或改写结构。

## 5. Python 调用

```python
import json
from pathlib import Path
from chronotrace_memory import query_bundle

bundle = json.loads(Path("examples/alice.json").read_text(encoding="utf-8"))
result = query_bundle(
    bundle, entity="Alice", attribute="home_city", intent="past",
    as_of="2026-02-01", known_at="2026-03-01",
    ledger_path="data/derived.sqlite3", scope="alice-demo",
)
print(result["answer_values"])  # ['Paris']
```

底层 `project()`、`validate_events()`、`Ledger` 和抽取 JSON schema 也可导入。底层 API 使用毫秒时间戳；推荐通过 `query_bundle` 做来源规范化。原研究中的本地模型抽取链路没有在基准上激活，当前发布版不调用模型，也不自动从自然语言生成 events。

## 6. 测试与研究复现边界

`examples/demo.py` 验证6项合成对照；测试套件包括18项冻结内核语义测试与新增的发布接口测试。两者均离线运行，不包含任何基准原文。

本仓库不能独立重跑原项目的288题 benchmark：基准数据、向量库、模型、exact32外部实现和原生评测脚本没有打包。保留的结果表是历史本地研究记录，公开版接口未经该套件重新评分。完整结论和运行资源恢复限制见 [RESEARCH_RESULTS.md](RESEARCH_RESULTS.md)。
