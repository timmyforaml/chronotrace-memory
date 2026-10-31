# 来源与改动披露

ChronoTrace Memory 的自动在线服务以 Context Weave / SourceTrail 0.32.0 为基础，原作者王子铭（Giorno-Banana），MIT许可；原作者声明及全部原归档文件原样保留。归档SHA256 `bff4443ee3cbdf4a5e320dfa56fb8e65ca7775d857550c4112de7ddb7a9c74fa`，对应项目提交 `e84af580a3a9a21f1eab6328d41e8b93bb52552e`。本候选不是从0.67迁移。直接复制的38个归档文件清单与逐文件散列见manifest.json；37项历史源码校验不含归档的SHA256SUMS.json。

新增独立模块：chronotrace_state.py（同来源明确状态对比/更正及查询投影）、chronotrace_store.py（不可变原文旁独立追加派生历史）、chronotrace_api.py（鉴权/同步HTTP服务入口）、aml_contract.py（Textual text数组与原始envelope幂等记录）。原版38文件未修改。额外派生不覆盖原始记忆；不把同词、同名、记录较晚或同一会话等同于同属性/当前状态。源内边界也不能证明现实中无限期有效，保留来源相对性及未核验的query-now状态。

参考Mem0固定本地SDK源码 `8d5b7865bd0521e75fe9ab1b260eeccc83f8a378`（mem0ai/mem0，Apache-2.0）：update/delete/history及SQLite history记录。先读适用AGENTS。本候选没有复制或嵌入Mem0 SDK源码，没有使用其托管服务，也不引用托管平台成绩作为SDK或本项目效果。

原版PROVENANCE.md还保留InvMem、ActiveMemoryIndex、ReFind、FlowGrid等历史研究来源及其技术报告链接。那些是基线作者的历史披露；不能据其中旧版本段落声称当前运行了LLM规划、事实抽取或更换了模型。当前在线Add/Search均无生成式LLM调用，Embedding固定text-embedding-v4 1024维；回答、提示和评分全部由平台统一执行。研究的本地Qwen Answer/Judge不属于线上服务。

仓库根目录v0.1.1为早期需结构化事件的离线手动内核；本online/v0.23-contract03目录单独提供在线服务的完整字节保真源码包，服务采用独立目录部署。旧公开内核、old native04b、release01、hypothesis04、contract03均是不同修订，不转移其成绩。没有发布评测原文/问题/金标、模型响应、数据库、权重、凭据或运行请求。外部依赖、模型及数据许可由各自权利人保留。

本文件只披露可从源码核验的事实。参赛者/团队本人署名、原创性与非重复实质提交、无操纵诚信承诺须由用户确认；准备脚本不代替本人作声明。
