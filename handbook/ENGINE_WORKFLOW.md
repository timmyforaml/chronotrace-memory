# 状态内核工作流

`state_engine/` 实现状态派生与时序处理，`contracts/` 保存生命周期契约。修改状态更新逻辑时，应先用合成场景检查生命周期行为，再核对发布材料。

在仓库根目录运行：

```shell
python -m pip install -e .
python -m unittest discover -s contracts -p "test_*.py"
python walkthroughs/demo.py
```

这些测试与演示不连接正式评测数据库，也不替代服务部署。实际接口、配置和运维约定分别见 [API.md](API.md) 与 [DEPLOYMENT.md](DEPLOYMENT.md)。

线上 v0.23 的复现使用 [固定版本运行指南](../online/v0.23-contract03/RUN_GUIDE.zh-CN.md)。其中的源码包、已记录补丁和清单决定该运行版本；开发内核不自动替换它。

校验开发树和固定材料时，可分别执行：

```shell
python contracts/verify_layout.py
python contracts/verify_layout.py --frozen-only
```

旧 `docs/` 入口保留对手册页面的引用。版本与来源说明见 [PROVENANCE.md](PROVENANCE.md)，项目许可见 [LICENSE](../LICENSE)。
