# Claude Commerce Agents

基于 Claude 构建的两个电商 agent：一个是商家嵌入自己应用中供顾客使用的**购物 agent**，
另一个是内部员工用来运营后台的**商家 agent**。每个 agent 只定义一次（prompt、技能、
工具合约、门控），可运行在 Messages API、Claude Agent SDK 和 Managed Agents 三种
路径上；四个可运行的行业示例展示了两个 agent 在同一套库上的效果。

> [!NOTE]
> 本项目中所有公司、品牌、产品和人物均为虚构，唯一的公司名是 ACME。
> 项目不会真正下单、扣款或更改线上商品：`checkout` 只渲染购物车内容交给宿主应用完成，
> 商家侧的每一次写操作都是暂存状态，需经人工审批后才会生效。业务规则、权限控制和
> 合规要求由部署方负责。

## 快速开始：运行示例

需要 Python 3.11+ 和 Node 22。克隆、安装、添加密钥、运行一个行业示例：

```bash
git clone https://github.com/anthropics/commerce-agents.git && cd commerce-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt       # 安装七个包及其锁定的依赖
cp .env.example .env                  # 添加 ANTHROPIC_API_KEY（如使用网关还需设置 ANTHROPIC_BASE_URL）
(cd examples && npm ci)               # 八个 web 应用共享一个 npm workspace
python scripts/run_demo.py retail     # API :8000 + 购物前端 :3000
```

`--merchant` 启动商家后台而非购物前端，`--all` 同时启动两者。可选的行业示例有
`retail`（:3000，后台 :3100）、`travel`（:3001，:3101）、`telecom`（:3002，:3102）
和 `entertainment`（:3003，:3103）；各示例的 README 中列出了可在两个界面上尝试的提示语。

## 快速开始：构建你自己的

Claude Code 插件可以基于这些包和你的系统脚手架生成一个 agent，也可以审查你已有的 agent。
按上述方式克隆仓库后（插件会将其作为参考读取）：

```bash
claude plugin marketplace add anthropics/commerce-agents
claude plugin install commerce-builder@claude-commerce-agents
claude
/scaffold-commerce-agent a shopping assistant for our store
```

该命令会询问你的技术栈、回放方案、然后构建项目；`/add-commerce-flow` 和 `/author-commerce-evals`
可在此基础上继续，`/review-commerce-agent` 则从已有的 agent 开始
（[`plugins/commerce-builder/`](plugins/commerce-builder/)）。每个命令在请求匹配其描述时
也会自动触发，因此不一定需要显式输入命令名。

## 两个 agent

**购物 agent** 负责搜索、比较、制定购物计划、填充购物车、回答订单和政策相关问题，
并记住顾客告知的信息。它的五个流程即 [`shopping-agent/skills/`](shopping-agent/skills/)
中的技能；部署时需要基于你的商品目录、购物车、订单和政策系统实现
[`StorefrontBackend`](shopping-agent/core/shopping_agent/backend.py) 接口。

**商家 agent** 负责解读业绩、维护商品信息、响应库存和订单提醒、定价促销以及起草营销活动；
每一次写操作都是暂存变更，由宿主应用的审批界面来执行。它的五个流程即
[`merchant-agent/skills/`](merchant-agent/skills/) 中的技能；部署时需要基于你的分析、
商品目录、库存、定价和营销系统实现
[`MerchantBackend`](merchant-agent/core/merchant_agent/backend.py) 接口。

## 目录结构

| 目录 | 内容 | pip 包名，`import` 名 |
|---|---|---|
| [`commerce-common/`](commerce-common/) | 两个角色共用的部分：配置、数据隔离、记忆、技能、grounding、展示组件、executor 框架、事件 | `commerce-common`, `commerce_common` |
| [`shopping-agent/core/`](shopping-agent/core/) | 购物类型定义、`StorefrontBackend`、prompt、工具合约、门控、executor | `shopping-agent-core`, `shopping_agent` |
| [`shopping-agent/runtime-messages-api/`](shopping-agent/runtime-messages-api/) | `ShoppingAgent`，基于 Messages API 的 turn 循环 | `shopping-agent-runtime`, `shopping_agent_runtime` |
| [`shopping-agent/runtime-agent-sdk/`](shopping-agent/runtime-agent-sdk/) | 基于 Agent SDK 的购物 agent，带控制台 | `shopping-agent-sdk`, `shopping_agent_sdk` |
| [`shopping-agent/managed-agents/`](shopping-agent/managed-agents/) | Managed Agents 的 manifest 和购物前端 MCP server | — |
| [`merchant-agent/core/`](merchant-agent/core/) | 商家类型定义、`MerchantBackend`、prompt、工具合约、变更护栏、门控、executor | `merchant-agent-core`, `merchant_agent` |
| [`merchant-agent/runtime-messages-api/`](merchant-agent/runtime-messages-api/) | `MerchantAgent` 和基于 Messages API 的分析委托 | `merchant-agent-runtime`, `merchant_agent_runtime` |
| [`merchant-agent/runtime-agent-sdk/`](merchant-agent/runtime-agent-sdk/) | 基于 Agent SDK 的商家 agent，带审批控制台 | `merchant-agent-sdk`, `merchant_agent_sdk` |
| [`merchant-agent/managed-agents/`](merchant-agent/managed-agents/) | Managed Agents 的 manifest、商家 MCP server、定时汇总 | — |
| [`examples/`](examples/) | 四个行业示例、共享宿主代码（`demo_common/`）、共享前端代码（`web-shared/`） | — |
| [`plugins/commerce-builder/`](plugins/commerce-builder/) | Claude Code 插件 | — |
| [`docs/`](docs/) | `safety.md`（强制规则）、`backends.md`（对接你的系统）、`deployment.md`（其他平台） | — |
| [`tests/`](tests/) | 跨包测试套件；各包也有自己的 `tests/` | — |
| [`scripts/`](scripts/) | `install.sh`、`run_demo.py`、`smoke_chat.py`、`screenshot_tour.py`、`check.py`、`deploy_managed_agent.sh`、`verify_all.py` | — |

## 三种运行方式

**Messages API。** 参考实现的循环；示例是围绕它构建的宿主应用：

```python
from pathlib import Path

from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

agent = ShoppingAgent(backend=your_backend, skills_dir=Path("shopping-agent/skills"),
                      config=ShoppingAgentConfig(brand_name="Your Store"))
async for event in agent.stream_turn(messages, session, state):
    ...   # text_delta, tool_call, ui, cart_update（商家侧为 change_update）, turn_complete
await agent.update_memory(messages, session)   # 记忆抽取；仅此路径支持
```

示例宿主应用通过 `X-Session-Id` 请求头传递 session id。

**Agent SDK。** 使用相同的 prompt、技能和工具，由 SDK 运行循环；宿主预取 grounding 所需的
数据，turn 结束后不再执行任何操作：

```bash
python shopping-agent/runtime-agent-sdk/main.py --once "a two-person tent under $250"
python merchant-agent/runtime-agent-sdk/main.py          # 通过 y/N 审批暂存的变更
```

**Managed Agents。** 托管的 agent，使用相同的技能和合约，调用你的 MCP server：

```bash
scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent   # 或 merchant-agent/...；--live 执行实际部署
```

## 安全

数据隔离、来源门控、上限、记忆验证和商家审批门控在工具调用内部执行，在三种路径上均生效；
grounding、分析预算和记忆抽取是运行时级别的功能。[`docs/safety.md`](docs/safety.md)
列出了每条规则及其所在模块和适用路径，以及部署时应首先添加的内容；示例没有身份认证，
MCP server 仅绑定到回环地址。

## 行业示例

| 示例 | 购物前端 | 商家后台 |
|---|---|---|
| [`examples/retail/`](examples/retail/) ACME | 搜索、比较、计划、购物车、结账、记忆，基于内置组件 | 汇总报告、暂存补货和商品修正、基于 SQL 视图的分析委托 |
| [`examples/travel/`](examples/travel/) ACME Travel | 按日期的库存和 `present_itinerary` 行程展示扩展 | 入住率日历和按日期窗口调整房价 |
| [`examples/telecom/`](examples/telecom/) ACME Mobile | 账户上下文、套餐矩阵、服务端生成的费用披露 | 套餐组合分析、标明受影响线路数的调价、受保护的监管费用 |
| [`examples/entertainment/`](examples/entertainment/) ACME Tickets | 限时锁票、候补名单、转让、场馆地图、全包费用披露 | 活动节奏分析、释放锁票以增加真实库存、保留费用的调价 |

每个示例的 README 都有 `Try` 部分：`scripts/smoke_chat.py` 运行的对话轮次，以及单条
提示语和对应的预期行为。

## 验证

```bash
ruff check . && ruff format --check . && pytest && python scripts/check.py
python scripts/verify_all.py                        # 上述命令加上部署 dry run 和 web 构建
python scripts/smoke_chat.py --vertical travel      # 一次实际对话；需要 API key
```

`requirements-dev.txt` 额外安装 pytest 和 ruff。CI 在两个 Python 版本上安装依赖、
构建八个 web 应用，并检查包名在公共索引上未被注册（锁定文件从本地目录安装，而非从索引
安装）。要确认缓存是否生效，可查看 `turn_complete` 中的 `cache_read_input_tokens`，
或各运行时日志中每次模型调用输出的那一行：第二轮为零表示前缀发生了变化。

## 部署到其他平台

运行时接受任意 `anthropic` 客户端作为 `client=` 参数，SDK 运行时从 CLI 环境获取平台
信息；[`docs/deployment.md`](docs/deployment.md) 涵盖了 GCP Vertex AI、AWS Bedrock、
Microsoft Foundry 和网关的部署方式。

## MCP 连接器

项目不附带任何 MCP 连接器；两个 agent 通过 Backend 接口访问你的系统。当某个官方连接器
是数据的权威来源时，它就是集成目标：分析数据仓库（Snowflake、BigQuery、Databricks、
Amplitude）、财务（Stripe、Square、PayPal、QuickBooks）、协作（Slack、Google Drive、
Gmail）。电商平台自身提供的用于商品目录、购物车或结账的 MCP server 在服务端通过
Backend 方法调用；在 Managed Agents 上，manifest 将其挂载在角色 server 旁边，
来源门控仍然拦截在每一次写操作之前。

## 定制你自己的 agent

- **Backend 方法。** 每个方法在服务端使用宿主为当前 session 持有的凭证调用你的服务；
  模型只读取返回结果。步骤顺序固定的流程应在 Backend 中强制该顺序。
- **阅读 Backend 指南。** [`docs/backends.md`](docs/backends.md) 详细介绍了身份认证与
  凭证、有序流程、结账对接、带选项的商品，以及你的平台无法提供的数据的处理方式。
- **同一套接口适配不同商业形态。** 在 marketplace 上，卖家是搜索的一个维度，商家 agent
  为当前 session 指定的运营方服务。对于账户或合同定价，报出的价格是当前 session 账户
  的专属价。如果没有自己的结账系统，可以关闭购物车或将其转为报价单、采购单或托管结账 URL。
- **结账只是交接。** 结账卡片链接到你自己的结账路由，或链接到平台的托管结账 URL
  （marketplace 上每个卖家一个）。Backend 返回 URL，宿主应用渲染；模型永远看不到该 URL。
- **从小处开始。** 购物 agent 的最小试点只需实现搜索和商品详情，其余方法用 stub 代替；
  stub 方法返回不可用的结果，且不改变 prompt 的任何字节。商家 agent 的最小试点只需实现
  八个读方法并让写操作拒绝；汇总和指标分析即可运行，无需写入路径。
- **关掉你没有的功能。** 业务上不具备的系统（如引流页面上没有购物车、没有订单追踪）通过
  `enable_*` 开关关闭，这会在所有路径上移除对应的工具、prompt 文本和 grounding 规则；
  将依赖该功能的流程放到 `skills/_staged/` 下。商家配置中对商品编辑、库存、定价和营销
  活动有相同的开关。
- **添加你自己的功能。** 一个流程就是 `skills/` 下的一个包含 `SKILL.md` 的目录。领域
  UI 通过 `PresentationExtension` 实现（行业示例中有七个）。`brand_name`、
  `assistant_name` 和 `brand_voice` 可在任一角色的配置中设置身份标识。

## 许可证

Copyright 2026 Anthropic PBC。基于 [Apache License 2.0](./LICENSE) 授权。
本项目为参考实现，不进行维护，不接受贡献。
