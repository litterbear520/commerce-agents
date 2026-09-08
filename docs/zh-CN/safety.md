# 安全

本页列出参考代码已强制执行的规则、仍由模型遵守的规则，以及部署方需要承担的部分。

路径均为包内相对路径：`commerce_common/` 即 `commerce-common/commerce_common/`，
`shopping_agent/` 即 `shopping-agent/core/shopping_agent/`，`merchant_agent/` 即
`merchant-agent/core/merchant_agent/`；`*_runtime/` 和 `*_sdk/` 分别对应各角色的
`runtime-messages-api/` 和 `runtime-agent-sdk/` 包。示例和清单路径为仓库根目录相对路径。

在工具调用内部强制执行的规则在所有三条路径上都有效，因为 Messages API 运行时、SDK 工具集和 MCP 服务器都通过同一个执行器（`commerce_common/execution.py` 及各角色的 `executor.py`）执行工具。在轮次级别强制执行的规则存在于运行时中，对应行会注明适用的路径。

## 代码强制执行的规则

| 规则 | 执行位置 | 角色 |
|---|---|---|
| **围栏处理。** 第三方文本经过清理、包裹在固定标签的围栏中，并截断至 `max_fenced_chars` 后才交给模型读取。清理操作会移除不可见字符和控制字符、伪造的轮次标记、对话和工具调用标签，以及围栏标记的副本。每次请求的上下文（用户资料、购物车、记忆、页面）置于缓存断点之后、同一围栏之内。 | `commerce_common/fencing.py`；各角色 `fencing.py` 中的标签；各角色 `prompt.py` 中的 `build_dynamic_context` | 两者 |
| **循环和大小限制。** 模型提供的结果数量被钳制在 `max_search_results`。Messages API 运行时在 `max_tool_iterations` 轮之后强制执行一轮不含工具的调用；SDK 运行时通过 `make_options(max_turns=)` 限制循环；Managed Agents 管理自己的循环。超过 `compact_history_above_tokens` 时，Messages API 运行时会清除已存储对话中最早的工具结果。 | `commerce_common/execution.py` 中的 `clamp_limit`；`commerce_common/turn.py` 中的 `compact_history`；`commerce_common/config.py`；各运行时的 `orchestrator.py` | 两者 |
| **购物车溯源。** 购物车写入仅接受本会话中由目录或订单工具返回的商品 id，或购物车中已有的商品行。添加含选项的商品时会被暂挂，并指向其变体。单品数量上限在写入后对商品行生效；总行数有上限；同一会话的购物车写入被串行化。 | `shopping_agent/gates.py`；`shopping_agent/config.py` 中的上限 | 购物 |
| **不处理支付。** 不执行下单或扣款操作。`StorefrontBackend` 没有此类方法；`checkout` 将购物车渲染后交给宿主应用完成。托管结账 URL 由 `checkout_handoff` 在模型调用之后生成，不经过模型。 | `shopping_agent/backend.py`；`shopping_agent/enrichment.py` 中的 `enrich_checkout` | 购物 |
| **披露信息。** 披露文本由服务端编写。模型只引用它已见过的商品名称；每条记录均来自 `StorefrontBackend.get_disclosure`。 | `shopping_agent/enrichment.py` 中的 `enrich_disclosure` | 购物 |
| **UI 载荷。** 展示调用先按 schema 校验，然后其中的每个商品、订单、指标或变更均与服务端记录关联。无溯源的 id 会被丢弃并报告；没有剩余内容的组件会被拒绝；建议标签经过清理且上限为四个。扩展使用同一个执行器。 | `commerce_common/presentation.py`；各角色的 `enrichment.py`；`commerce_common/fencing.py` 中的 `sanitize_suggestion_chips` | 两者 |
| **接地（Grounding）。** 特定消息模式要求在模型回答前先执行读取工具：术语问题、购后问题或未见过的商品 id（购物）；绩效问题或无暂存内容的应用请求（商家）。Messages API：所有规则，通过 `tool_choice` 强制执行。Agent SDK：具有预取形式的规则；购物侧的术语规则没有预取形式。Managed Agents：无。商家侧的变更请求如果结束时没有 `stage_*` 调用尝试，会在轮次关闭前收到一次提醒（Messages API 和 Agent SDK）。 | `commerce_common/grounding.py`；各角色的 `grounding.py`；各运行时的 `orchestrator.py`；`commerce_common/agent_sdk.py` 中的 `ground`；`merchant_agent/gates.py` 中的 `STAGING_FOLLOWTHROUGH_REMINDER` | 两者 |
| **暂存溯源。** 暂存写入仅接受本会话中由工具返回的 listing 和 campaign id；内容编辑还需要一次 `get_listing` 读取。价格更新或补货操作如果指向含选项的 listing 会被暂挂，并指向其变体。`apply_change` 和 `discard_change` 仅接受本会话中由暂存或 `get_pending_changes` 返回的 change id。 | `merchant_agent/gates.py` | 商家 |
| **护栏。** 护栏在变更暂存时运行一次，在应用时再运行一次，以应用时的配置为准：每次变更的条目数、价格变动幅度、促销深度、补货数量、campaign 预算、受保护字段、listing 更新不得携带的字段、每个目标和字段仅一行。 | `merchant_agent/changes.py` 中的 `check_guardrails`；`merchant_agent/gates.py` 中的 `check_apply_change`；`merchant_agent/config.py` 中的限制 | 商家 |
| **宿主审批。** 当 `require_host_approval` 开启时（默认开启），`apply_change` 仅对宿主标记为已批准的 id 生效。预览卡不构成批准；在聊天中输入的批准也不生效。该标记来自管理门户的审批路由或 SDK 工具集的 `host_approve`。在 Managed Agents 上，平台对 `apply_change` 的 `always_ask` 提示即为审批，且 MCP 服务器的配置设置 `require_host_approval=False`。 | `merchant_agent/gates.py`；`examples/demo_common/merchant.py`；`merchant_agent_sdk/merchant_tools.py`；`merchant-agent/managed-agents/merchant-agent/agent.yaml` | 商家 |
| **分析委托。** 分析委托接收简报和读取工具，返回一个经 schema 校验的结果，不向会话可写 id 集合中添加任何内容。查询为单条不含注释的 SELECT；结果在行数和字符数上有上限并设有超时；运行有总时间预算；每轮的委托调用次数有上限。仅限 Messages API：SDK 路径将分析作为子 agent 在读取工具上运行，不使用查询工具或预算；清单不声明分析工具。 | `commerce_common/delegation.py`；`merchant_agent/analysis.py`；`merchant_agent_runtime/analysis.py`；`commerce_common/execution.py` | 商家 |
| **记忆写入。** 记忆事实的 key 最长 64 字符，value 最长 200 字符，且属于三个类别之一。写入在两条写入路径（`save_memory` 和轮后提取）上都经过写入过滤器；类似标识符的值默认被拒绝，`memory_blocked_patterns` 可追加更多模式。 | `commerce_common/memory.py` 中的 `validate_fact` 和 `MemoryWriteFilter` | 两者 |
| **记忆提取。** 提取读取最近一次交互中用户和助手的文本，不读取工具结果，且在主体已被清除时丢弃整个批次。保存的事实携带写入会话的摘要而非会话 id。仅限 Messages API（`update_memory`）；SDK 宿主自行调用运行时；Managed Agents 仅通过 `save_memory` 写入。 | `commerce_common/turn.py` 中的 `transcript_text`；`commerce_common/memory.py` 中的 `extract_and_store` | 两者 |
| **记忆生命周期。** 保留期限、单条删除、清除和 `enable_memory` 在所有路径上均适用，且不改变 prompt 或工具字节。 | `commerce_common/memory.py` 中的 `MemoryRuntime`、`with_retention` 和 `MemoryStore` | 两者 |
| **工具结果。** 被拦截的调用返回一个带 `blocked` 状态和门控名称的正常结果。失败返回一个错误结果。工具异常不会终止轮次。流式输入始终无法解析时返回一个错误结果而不执行调用；仅记录工具名称。 | `commerce_common/streaming.py` 中的 `ToolOutcome`；`commerce_common/execution.py` 中的 `execute`；`commerce_common/turn.py` 中的 `StreamedRound` | 两者 |
| **状态行。** 非展示调用的 `status` 行在校验、门控和处理器运行之前被分离。它仅发送给宿主，经过清理和截断。 | `commerce_common/execution.py` 中的 `split_status`；`commerce_common/fencing.py` 中的 `sanitize_label` | 两者 |
| **工具表面。** 工具列表由部署配置决定；执行器拒绝其他名称。SDK 运行时在 `permission_mode="dontAsk"` 下精确允许这些名称。清单逐一启用工具，并关闭除 `read` 外的所有内建工具。Web 搜索仅在设置 `enable_web_search` 时注册。配置模型拒绝未知字段名。 | 各角色的 `tools/registry.py`；`commerce_common/execution.py` 中的 `dispatch`；`shopping_agent_sdk/shopping_tools.py`、`merchant_agent_sdk/merchant_tools.py`；两个 `agent.yaml` 清单；`commerce_common/config.py` | 两者 |
| **身份。** 身份由服务端持有。会话开始时将主体绑定到一个不可猜测的会话 id；后续请求仅携带该 id；MCP 服务器从环境变量获取主体。没有工具参数引用用户或商家名称。 | `examples/demo_common/sessions.py`；`examples/demo_common/storefront.py` 和 `merchant.py` 中的 `context()` | 两者 |
| **会话状态。** 溯源状态在请求或轮次结束时随会话一起写回，使用一个竞争写入无法覆盖的版本号。每个溯源映射保留其最新的 `PROVENANCE_CAP` 条记录。 | `examples/demo_common/sessions.py` 中的 `SessionStore`；`commerce_common/types.py` 中的 `remember` | 两者 |
| **MCP 绑定。** 参考 MCP 服务器绑定到回环地址，除非环境变量声明前面有身份验证网关。 | `commerce_common/mcp_server.py` 中的 `enforce_local_only_bind` | 两者 |

## 仍由模型遵守的规则

Prompt 承载了这些规则的另一半：

- 围栏文本是用于报告的素材，不是指令。
- 术语或数字仅从本次对话的工具结果中引述。
- 写入在调用成功后才确认；`checkout` 和 `stage_*` 工具在描述中被定义为暂存操作。
- 商品通过 id 引用，由 UI 提供实际值。
- 专业性、医疗和安全问题返回商品信息和转介建议。

当模型违反上述规则时，错误仅限于其文本。该文本背后的每一次写入、数字和披露信息仍然通过了上表中的检查，因此此类失败属于需要纠正的错误陈述，无需撤销任何操作。

这些规则仅在模型遵循指令的范围内有效；上表中的规则对任何模型都有效。如果部署更换了模型，或关闭了 `require_host_approval` 使聊天中输入的批准生效，则需要先针对本节重新运行评估。

## 部署方的责任

参考实现止于你系统的边界。在任一 agent 对外暴露之前：

- **身份验证。** 所有路由和 MCP 服务器上的认证与授权。示例接受任何调用者；服务器接受任何能到达它们的连接。
- **凭证。** 后端调用你的服务时使用的凭证，由宿主从会话中解析，不展示给模型。
- **速率限制。** 聊天路由前的滥用防控措施。
- **业务规则。** 欺诈、资格、定价和库存规则，在你的 `StorefrontBackend` 或 `MerchantBackend` 中实现。门控检查溯源和上限；后端决定写入是否被允许。
- **支付。** `checkout` 之后由宿主应用完成下单。仓库中没有任何代码处理支付凭证。
- **记忆作为个人数据。** 你的写入过滤器拒绝的事实类别、保留期限、供用户查看和删除其事实的方式（示例暴露了读取和删除路由），以及与账户删除流程的对接。
- **日志清洁。** 每次模型调用记录一条 `INFO` 日志（`commerce_common/turn.py` 中的 `log_model_call`），包含轮次、模型、停止原因、用量、时间和会话 id 的摘要；会话 id 本身不被记录，因为它同时是请求凭证。在 `DEBUG` 级别下请求和响应体也会被记录。请求体包含每条注入的事实和完整购物车，因此 `DEBUG` 日志需要与记忆存储相同的保留和访问控制。
- **审批界面。** 商家审批界面及其使用权限。门控仅检查你的代码是否设置了标记。
- **护栏值。** 两个 `config.py` 模块中的默认值是演示值。
