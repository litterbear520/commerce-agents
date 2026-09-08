# 部署平台

代码默认调用 Anthropic API。每种运行时路径都有一个地方可以将其指向 GCP Vertex AI、
AWS Bedrock、Microsoft Foundry 或内部网关。以下内容适用于两个角色；示例使用购物端
的名称，`MerchantAgent`、`merchant_agent_sdk` 和 `merchant-agent/managed-agents/`
可一一对应替换。

## 支持矩阵

| 路径 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|
| Messages API 运行时 | 是 | 是 | 是 | 是 | 是 |
| Agent SDK 运行时 | 是 | 是 | 是 | 是 | 是 |
| Managed Agents | 是 | 否 | 否¹ | 否 | 是² |
| 商家分析，托管代码执行 | 是 | 否 | 否 | 是³ | 否 |
| 商家分析，`execute_analysis_query` | 是 | 是 | 是 | 是 | 是 |

各路径选择平台的方式：

| 路径 | 设置位置 | Anthropic API | GCP Vertex AI | AWS Bedrock | Microsoft Foundry | 内部网关 |
|---|---|---|---|---|---|---|
| Messages API 运行时 | agent 的 `client=` | 默认 | `AsyncAnthropicVertex` | `AsyncAnthropicBedrockMantle` 或 `AsyncAnthropicBedrock` | `AsyncAnthropicFoundry` | `AsyncAnthropic(base_url=..., auth_token=...)` |
| Agent SDK 运行时 | `options.env` | 默认 | `CLAUDE_CODE_USE_VERTEX=1` | `CLAUDE_CODE_USE_BEDROCK=1` 或 `CLAUDE_CODE_USE_MANTLE=1` | `CLAUDE_CODE_USE_FOUNDRY=1` | `ANTHROPIC_BASE_URL` |
| Managed Agents | 部署脚本的 `ANTHROPIC_API_URL` | 默认 | — | — | — | `ANTHROPIC_API_URL` |

¹ 见下方 AWS 说明。² 通过一个透传代理为部署脚本和 session 端点服务；见"Managed Agents：
端点"部分。³ 仅限托管在 Anthropic 上的 Foundry 部署。

两行分析相关的条目适用于开启了 `enable_analysis` 的商家部署。托管代码执行
（`analysis_use_code_execution`）挂载 `code_execution_20260120` 服务端工具，
由 Anthropic API 提供；托管在 Anthropic 上的 Foundry 部署也提供该工具。
`MerchantBackend.execute_analysis_query` 在你的基础设施中运行并返回普通的工具结果，
因此适用于所有平台。零售示例使用查询方法，仅在设置 `MERCHANT_ANALYSIS_CODE_EXECUTION=1`
时挂载沙盒。

AWS 说明：Managed Agents 运行在 Anthropic 运营的基础设施上，因此没有 Vertex、Bedrock
或 Foundry 变体。在 AWS 上可通过
[Claude Platform on AWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
使用，它提供相同的 `/v1` 端点，使用 AWS 认证、`anthropic-workspace-id` 请求头和第一方
模型 id。部署脚本不发送这两者；请参考该平台指南。

## 模型 id

模型是配置中的一个字符串。每个角色配置有 `model` 和 `memory_model`；商家配置额外有
`analysis_model`。SDK 运行时将模型复制到其 options 中，manifest 在 `agent.yaml` 中
设置。示例 API 在 `ANTHROPIC_MODEL` 非空时从中读取 `model`。没有其他地方读取该字符串，
因此切换平台只需修改配置。不同平台的 id 格式不同；请参照你的平台目录确认。

| 字段 | 仓库默认值 | Anthropic API、网关 | GCP Vertex AI | AWS Bedrock (Mantle) | AWS Bedrock (Invoke API) | Microsoft Foundry |
|---|---|---|---|---|---|---|
| 购物端 `model` | `claude-sonnet-5` | `claude-sonnet-5` | `claude-sonnet-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-sonnet-5` |
| 商家端 `model` | `claude-opus-5` | `claude-opus-5` | `claude-opus-5` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-opus-5` |
| `memory_model` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5@20251001` | `anthropic.<SERVED_MODEL>` | `<INFERENCE_PROFILE_ID>` | `claude-haiku-4-5` |

- Vertex 使用 `@` 分隔的日期快照。
- Bedrock 有两个端点。Mantle 使用 Messages API 协议，接受其自有列表中不带日期的
  `anthropic.` id；Invoke API 接受你账户目录中的推理配置 id
  （带区域前缀、日期和 `-v1:0` 后缀）。
- Foundry 接受你资源中的部署名称；上表中的值是默认值，与不带日期的第一方 id 一致。
- Managed Agents 接受第一方 id。
- 三个模型字段都经过同一个 client，因此三个都必须在目标平台上存在。

## Messages API 运行时：`client` 参数

`ShoppingAgent` 和 `MerchantAgent` 接受可选的 `client` 参数。不传时会构造
`AsyncAnthropic`，从环境变量读取 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 和
`ANTHROPIC_BASE_URL`；设置后两者（在环境变量或仓库根目录的 `.env` 中）可将示例 API
指向网关。传入 client 时，所有调用都使用它：turn 循环（`messages.stream`）、记忆抽取
和分析委托（`messages.create`）。`anthropic` 包中的任何异步 client 都适用。参数标注
为 `AsyncAnthropic`，因此类型检查器对平台类需要 `cast`。

```python
from pathlib import Path

from anthropic import (
    AsyncAnthropic,
    AsyncAnthropicBedrockMantle,
    AsyncAnthropicFoundry,
    AsyncAnthropicVertex,
)
from shopping_agent import ShoppingAgentConfig
from shopping_agent_runtime import ShoppingAgent

common = dict(backend=your_backend, skills_dir=Path("shopping-agent/skills"))

# GCP Vertex AI：pip install "anthropic[vertex]"；使用应用默认凭证。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5@20251001"),
    client=AsyncAnthropicVertex(project_id="your-project", region="global"),
)

# AWS Bedrock，Mantle 端点：使用标准 AWS 凭证链。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(
        model="anthropic.your-served-model", memory_model="anthropic.claude-haiku-4-5"
    ),
    client=AsyncAnthropicBedrockMantle(aws_region="us-east-1"),
)

# Microsoft Foundry：使用 Azure API 密钥，或通过 azure_ad_token_provider= 使用 Entra ID。
agent = ShoppingAgent(
    **common,
    config=ShoppingAgentConfig(memory_model="claude-haiku-4-5"),
    client=AsyncAnthropicFoundry(resource="your-resource", api_key="your-azure-key"),
)

# 内部网关：必须提供带 SSE 流的 /v1/messages 接口。
agent = ShoppingAgent(
    **common,
    client=AsyncAnthropic(base_url="https://llm-gateway.internal.example", auth_token="your-token"),
)
```

这些包声明 `anthropic>=0.91`，即添加了 `AsyncAnthropicBedrockMantle`（上述 client 类
中最新的一个）的版本。

## Agent SDK 运行时：CLI 环境

SDK 运行时不构造 HTTP client。`claude-agent-sdk` 启动 Claude Code CLI，CLI 根据
环境变量选择平台。`make_options()` 返回 `(options, toolset)`；在打开 client 之前将
平台变量添加到 `options.env` 中。SDK 将 `env` 叠加到继承的环境上，因此只需列出平台
变量。

```python
from claude_agent_sdk import ClaudeSDKClient
from shopping_agent_sdk import make_options

options, toolset = make_options()
options.env.update({"CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1"})
options.model = "us.anthropic.claude-sonnet-5"
async with ClaudeSDKClient(options=options) as client:
    ...
```

| 目标 | 必需 | 凭证 | 模型 id | 可选 |
|---|---|---|---|---|
| AWS Bedrock，Invoke API | `CLAUDE_CODE_USE_BEDROCK=1` | AWS 标准链 | 推理配置 id | `ANTHROPIC_BEDROCK_BASE_URL` |
| AWS Bedrock，Mantle | `CLAUDE_CODE_USE_MANTLE=1` | AWS 标准链 | `anthropic.` id | `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`、`CLAUDE_CODE_SKIP_MANTLE_AUTH`⁴ |
| GCP Vertex AI | `CLAUDE_CODE_USE_VERTEX=1`、`ANTHROPIC_VERTEX_PROJECT_ID`、`CLOUD_ML_REGION` | 应用默认凭证 | `@` 日期 id | `ANTHROPIC_VERTEX_BASE_URL` |
| Microsoft Foundry | `CLAUDE_CODE_USE_FOUNDRY=1`、`ANTHROPIC_FOUNDRY_RESOURCE` 或 `ANTHROPIC_FOUNDRY_BASE_URL` | `ANTHROPIC_FOUNDRY_API_KEY`，或通过 Azure 默认链使用 Entra ID | 部署名称 | `ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`⁵ |
| 内部网关 | `ANTHROPIC_BASE_URL` | `ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY` | 第一方 id | `ANTHROPIC_CUSTOM_HEADERS` |

⁴ 当网关负责签名请求时设为 `1`。⁵ 固定 CLI 用于 Sonnet 和 Opus 调用的部署名称。

当平台需要为 CLI 的小模型调用使用自己的 id 时，设置 `ANTHROPIC_DEFAULT_HAIKU_MODEL`。
这些变量属于 Claude Code；其文档是权威参考。

## Managed Agents：端点

`scripts/deploy_managed_agent.sh` 读取 `ANTHROPIC_API_KEY` 并向 `ANTHROPIC_API_URL`
（默认 `https://api.anthropic.com`；另外两条路径读取 `ANTHROPIC_BASE_URL`）发送请求。
该地址的网关必须代理 `/v1/skills`（multipart）、`/v1/agents`，以及为宿主应用代理
`/v1/environments`、`/v1/sessions` 和 session 事件流，并保留 `anthropic-beta` 请求头。
仅代理 `/v1/messages` 的网关不支持此路径。

```bash
# 通过网关进行 dry run（默认）；添加 --live 执行实际部署。
ANTHROPIC_API_URL=https://llm-gateway.internal.example \
  scripts/deploy_managed_agent.sh shopping-agent/managed-agents/shopping-agent
```

## 测试覆盖

`tests/test_platform_seams.py` 使用占位凭证构造每个平台的 client，检查两个 Messages API
运行时是否绑定了该 client，以及上述各环境变量是否在两个 SDK 运行时中到达
`ClaudeAgentOptions`。`scripts/verify_all.py` 运行两个部署 dry run。没有任何测试
持有云凭证，因此这里不会运行实际的平台对话；在依赖之前请在你的平台上运行一次。要在
完全没有凭证的情况下驱动任一 agent，可使用 `commerce_common.testing.FakeClient`
来脚本化模型。
