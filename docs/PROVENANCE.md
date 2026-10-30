# 来源、版本与发布边界

## 本项目

ChronoTrace Memory v0.1.1 源自独立状态生命周期研究。发布版内核 `src/chronotrace_memory/lifecycle.py` 保留冻结实现，SHA-256：

`46be8945a381553fcb42e02ab631fdb890976fb8e0fe66ef3313aace5e4abcd5`

原始18项测试仅修改了模块导入路径；包装层、命令行、合成JSON示例、文档和接口测试为发布时新增。发布说明和来源散列不包含账户、密钥或本机私有路径。

## exact32 对照身份

- exact官方版本：0.32.0，未使用后续0.67分支。
- incumbent源码提交：`e84af580a3a9a21f1eab6328d41e8b93bb52552e`。
- 源码归档SHA-256：`bff4443ee3cbdf4a5e320dfa56fb8e65ca7775d857550c4112de7ddb7a9c74fa`。
- 原项目验证37个原始源码文件，development Search/input哈希复现288/288。
- exact32源码、基准数据及模型不随本仓库分发；本仓库MIT许可不扩展到这些外部材料。

## Mem0 参考身份

固定本地快照：[mem0ai/mem0 @ 8d5b7865bd0521e75fe9ab1b260eeccc83f8a378](https://github.com/mem0ai/mem0/tree/8d5b7865bd0521e75fe9ab1b260eeccc83f8a378)。已先读取仓库及包目录适用AGENTS.md。

参考范围：`mem0/memory/main.py` 的 `_update_memory`、`_delete_memory`、`history`，以及 `mem0/memory/storage.py` 的 `SQLiteManager.get_history`。上游更新/删除向量条目并另记历史，本实现独立添加不可变原文、派生账本、有效时间/记录时间投影及更正目标区间继承；不声称这些双时间语义原样来自上游SDK。

上游为Apache-2.0许可。本仓库没有复制或内嵌Mem0代码，也不运行其SDK；原快照中预先存在的qdrant改动未使用、未修改。没有将Mem0托管平台成绩作为开源SDK或本项目成绩。

旧词法更正链在288题中输入0变化，探索Smoke未见目标收益，作为失败背景保留。本次内核改变了表示与投影语义；其自动检索集成仍未在基准上激活，结果不能因机制不同而宣称有提升。

## 原始材料保护

公开仓库仅包含自行实现的代码、纯合成例子及必要聚合结果。没有发布原始对话、评测题目/提示、参考答案、模型响应、数据库、模型权重、认证信息或旧运行日志。原研究的冻结文件不因公开包装而被修改。SHA-256清单见 [source-manifest.json](source-manifest.json)，以提交中的UTF-8/LF文件字节为准，清单本身不递归包含自身。

v0.1.0清单曾按Windows工作目录字节生成，Git换行归一化后部分非内核文件哈希不一致；v0.1.1统一LF并修复清单。初始版本和修复记录均保留，内核散列与冻结评分没有变化。
