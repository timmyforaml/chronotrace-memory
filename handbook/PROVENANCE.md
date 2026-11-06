# 版本与发布记录

参赛者已提交 ChronoTrace Memory v0.23 的 Textual Full。本次说明更新日期为 2026-11-04；提交状态依据参赛者确认，最终成绩和公榜状态以平台为准。

## 在线 v0.23 / contract03

| 标识 | 值 |
|---|---|
| 原始固定发布 commit | [`e98032224d608937b6afece8f28ea5f1dd415069`](https://github.com/timmyforaml/chronotrace-memory/tree/e98032224d608937b6afece8f28ea5f1dd415069) |
| 在线修订 | `source-local-extents-01.contract03` |
| 原压缩包 SHA256 | `d3a93e76dec07dde5bf9319189db10c6fb982b507ec24361c13e1d83a915025d` |
| 原始源码清单 SHA256 | `027b67c8fcb81674da70eaac1f8573632c033b95813dc82714d715e640a7fbd1` |
| 后续已记录 Full 服务清单 SHA256 | `4f7aa733e817f906605e6c9ef88c6a5f9e39ef54e5acaa2283e1f6ac997d8429` |
| 后续 `remote_encoder.py` SHA256 | `3959e2d8c8d3d95aa1e92f553bcfe59d8670dd39ed7e2b3a6a274157beea3174` |

原始 `source.tar.gz`、`manifest.json`、`package.json` 是 2026-10-31 发布快照，保留原样；其中 `Full_submitted: false` 等状态只反映打包时点，不表示今天的任务状态。

公开仓库已包含线上使用的超长输入兼容性修复，线上部署与公开实现采用相同的 v0.23 核心方法和接口。2026-11-01 运维记录核验的修复位于 `adaptive_evidence/remote_encoder.py`：识别供应方明确的长度错误，对完整 UTF-8 文本无损分段，用同一模型处理，按字节数加权合并并归一化；其他错误继续失败。普通成功输入保持原路径，超长输入按分段结果计算向量。上表分别保留发布快照与默认还原代码的文件校验信息。

`online/v0.23-contract03/recorded-length-repair/` 保存精确文件副本及 42 文件校验清单。`prepare_source.py` 校验原压缩包、应用这一个副本、核验全部文件并生成真实 manifest。这是本地复现工具，不更新服务、不重新打包原压缩包；工具自身及文档不计入已记录的服务源码身份。`--archive-only` 可还原原始快照。

清单身份算法：对 `source_files_sha256` 映射执行 `json.dumps(mapping, sort_keys=True, separators=(',', ':'))`，UTF-8 编码后计算 SHA256。`manifest.json` 自身不计入映射，避免自引用。部分源文件含 CRLF，必须按字节校验，不做换行归一化。目录名和 Health 哈希仅作辅助，实际文件校验优先。

## 离线 v0.1.1

根目录 `state_engine/chronotrace_memory`、`pyproject.toml`、`walkthroughs/` 和 `contracts/` 是独立的标准库结构化状态内核，需要显式事件，不是在线 HTTP 服务入口。冻结研究见 [RESEARCH_RESULTS.md](RESEARCH_RESULTS.md)，离线文件清单见 [source-manifest.json](../docs/source-manifest.json)。

## 本次补充

更新 README、安装、接口、部署和版本说明，补充已有修复的复现附件，不修改运行中的服务或评测数据。文档分别标明测试、Smoke、本地研究及 Full 状态。源码附带的许可证及版权声明保留，未公开凭据、题目、答案、数据库、模型或私有日志。
