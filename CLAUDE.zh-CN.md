# commerce-agents

给在这个仓库里工作的 agent 看的，包括 commerce-builder 插件的使用者。这是 Claude 上
电商 agent 的公开参考实现：两个 agent（购物和商家），各有三种运行路径，四个行业示例，
以及一个 Claude Code 插件。

## 目录结构

- `commerce-common/commerce_common/`：两个角色共用的部分；其 `__init__` 列出了所有模块。
- `shopping-agent/core/shopping_agent/`：类型定义、`StorefrontBackend`、配置、prompt、`tools/`、门控、enrichment、executor。
- `merchant-agent/core/merchant_agent/`：商家侧的对应物，额外有 `changes.py` 和 `analysis.py`。
- `*/skills/`：每个角色五个流程，每个流程一个 `SKILL.md`。
- `*/runtime-messages-api/`：`ShoppingAgent`、`MerchantAgent`、商家分析委托。
- `*/runtime-agent-sdk/`：每个 agent 以 `ClaudeAgentOptions` 的形式定义，带控制台。
- `*/managed-agents/`：manifest 目录（含派生的 `system.md`）和该角色的 MCP server。
- `examples/demo_common/` 和 `examples/web-shared/`：各行业示例的 API 和 web 应用共用的部分；`examples/` 是 npm workspace。
- `examples/<vertical>/`：`api/`、`data/`、`storefront-web/`、`merchant-web/`；端口 8000-8003、3000-3003、3100-3103。
- `plugins/commerce-builder/`：六个技能、四个命令；`.claude-plugin/marketplace.json` 指向它。
- `docs/`：`safety.md`、`backends.md`、`deployment.md`。`scripts/`：安装、demo、冒烟测试、截图、检查、部署、验证。
- `tests/`：跨包的测试套件（两个角色在三种路径上都测）；各包也有自己的 `tests/`。

`requirements.txt` 安装七个包及其锁定的依赖（`requirements-dev.txt` 额外安装 pytest
和 ruff）；`scripts/install.sh` 执行安装。

## 设计规则

- 一个模型掌控整个对话；一条规则放在工具描述、prompt 还是技能中，取决于它的适用频率。
- 静态 prompt 和 `tools[]` 在每个 turn 上是完全相同的字节；每次请求特有的数据放在缓存断点之后的隔离块中。
- UI 是展示工具调用，由服务端校验和填充，以 `ui` 事件流式推送。
- 第三方内容是被隔离的数据；写操作由来源门控和代码级上限保护；`checkout` 不扣款；商家写操作只能通过宿主审批生效。
- 核心是领域无关的；行业示例通过 `PresentationExtension` 添加 UI，其余自行管理。
- 每个机制只定义一次，在 `commerce_common` 或角色核心中，由三种路径共享。

## 虚构与原创

不出现任何真实的公司、品牌、产品或人物：唯一的公司是 ACME 及其产品线；所有品牌、
prompt、schema 和数据均为本项目原创。两个例外：部署和集成目标（README 的"MCP 连接器"
部分；`docs/deployment.md` 中的平台和 SDK 名称、README 的部署部分，以及平台测试），
以及与图片相邻的 `IMAGE-CREDITS.md` 中列出的 CC0 分类照片。拿不准时，重新设计而非改名。

## 约定

- Python 3.11+，`ruff`（根目录 `ruff.toml`），`pytest`（根目录 `pytest.ini`），类型注解，`pydantic` schema；web 应用使用 Next.js 和 TypeScript。
- 技能描述使用请求类名，不带示例话术；工具描述说明工具的适用场景；示例保持结构化。
- 对 prompt 文本、工具描述、技能或隔离通知的修改需要重新派生 `system.md`；`scripts/check.py` 进行比对。
- 文风：使用直白的陈述句；每个概念只用一个术语；每个事实只出现一次并标明所在模块；每个角色使用自己的术语；README 说明一个东西是什么、怎么运行、接口在哪里；不写历史、日期或过程叙述；能删则删，不要重新措辞。
- 新增模块时需更新本文件和对应的 README。

## 验证

```bash
ruff check . && ruff format --check . && pytest && python scripts/check.py
python scripts/verify_all.py          # 上述命令加上部署 dry run 和 web 构建
```
