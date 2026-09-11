# 构建路线图审阅意见

供修改 `BUILD_ROADMAP.md` 的 agent 使用。基于 2026-09-11 的路线图、关键源码及官方博客核查；未运行全量测试或付费模型评估。下文 Step 编号对应当前路线图，代码路径相对仓库根目录。

## 目标与修改边界

用户希望从零逐步构建整个项目，理解生产级 agent 产品的诞生过程，并在实现中查漏补缺。当前路线图适合复建参考仓库，但生产实践与模型评估闭环不足。

保留现有主线：直接 API → 工具循环 → 门控 → 模块化 → 第二角色与共享层 → 行业和运行时扩展。优先做局部调整，保留全部项目学习范围；教学顺序应表述为建议路径，而非作者实际开发历史。

## 优先调整

1. **前置成功标准与评估。** 增加 Step 00：首个用户场景、成功条件、禁止结果、小型任务集。Step 02–04 开始累积真实模型 eval，每阶段比较最终状态、成功率、延迟、工具轮数和每个成功任务的成本。先做断言与人工检查，再加入多次运行、模型裁判及模型配置对比。仓库 `plugins/commerce-builder/skills/commerce-evals/SKILL.md` 明确不附带 eval harness；写评估插件不等于建成评估体系。
2. **测试和基础 CI 随能力建立。** Step 04 溯源、Step 06 数量上限当步补测试；Step 09–10 建基础 CI，Step 30 再扩展完整矩阵。测试稳定的行为约束，避免以“接口未稳定”为由推迟全部测试。
3. **提前完成薄的产品闭环。** 基础展示与流式循环就绪后，插入最小零售 Web：搜索 → 商品卡 → 加购 → 结算交接。完整 UI 和商户门户仍留在 Stage E，让交互问题早于全部后端机制完成时暴露。
4. **修复阶段依赖。** Step 12 先做商品展示，订单与结算组件随 Step 14 的类型和接口加入；Step 13 先启用已有工具支撑的技能，售后、记忆技能随能力启用。Step 16 拆成基础流式、恢复机制、性能优化。Step 18 可先写商户只读切片，再依据实际重复逐块提取共享层。
5. **增加生产实践阶段。** 现有 Step 33 完成应称“参考实现复建完成”。随后亲手接入真实或沙箱后端、认证授权、持久化与原子业务约束、幂等与重试、故障恢复、运行监测、灰度和回滚。三种运行时、四个行业、插件仍全部学习，但可以排在第一条生产闭环之后。

生产阶段至少验收：跨用户访问被拒绝；重复提交不重复执行；跨进程并发不突破业务限制；重启和断流后状态可恢复；记忆可查看、更正、删除；能定位失败并回滚发布。依据见 `docs/safety.md` 的部署者责任、`docs/backends.md`、`examples/demo_common/sessions.py`。单进程锁和内存会话不是完整生产存储方案。

## 已核实、应直接修正的问题

| 位置 | 修正要求 |
|---|---|
| Step 05 | 删除“清洗后模型不再被注入”的保证。离线运行确认示例中的自然语言恶意指令原样保留。围栏清洗处理标记和控制字符；行为仍须 eval，危险操作由代码门控。依据：`commerce-common/commerce_common/fencing.py`。 |
| Step 08、18 | 包根未导出示例中的类。分别使用 `shopping_agent.executor`、`commerce_common.fencing`、`commerce_common.execution`、`commerce_common.memory` 子模块导入。 |
| Step 11 | 缓存按 `tools → system → messages` 匹配前缀，不是三个独立缓存区；新增内容或缓存过期后仍可能出现 creation tokens。当前实现把动态上下文放第二个 system 块，变化会影响后续历史缓存；博客建议 volatile 内容放末尾，需解释差异。 |
| Step 15、21 | 中文示例不能证明默认英文词表触发了 grounding。改用实际可匹配的样例，或增加中文词表及测试；区分模型自行查询与代码强制查询。 |
| Step 16 | 即时工具执行发生在 `content_block_stop` 后，完整参数解析成功时；不是任意部分 JSON 一可解析就执行。预览与业务执行分开。依据：`commerce-common/commerce_common/turn.py` 的 `EagerDispatcher`。 |
| Step 20 | `29.99 → 39.99` 涨幅约 33.34%，超过默认 20% 护栏，应作为拒绝用例，或更换合法涨价示例。 |
| Step 23、26 | 删除路径中重复的 `demo_common`；零售组件注册表实际在 `examples/retail/storefront-web/components/generative/index.tsx`。 |
| Step 28 | 一致性测试覆盖部分工具合约、搜索结果等，不能推出三条路径完整行为相同。grounding、分析和记忆提取的差异见 `docs/safety.md`。 |
| Step 31 | 平台接缝测试与部署 dry-run 不代表真实平台验证通过。`docs/deployment.md` 明确没有运行真实云平台对话。 |

## 修改后的验收标准

- 每步只依赖此前已实现的能力，结束时有可运行、可观察的结果；重步骤拆为独立验收的小步。
- 给重要简化补一句“当前限制、替换时机及验证方式”，例如内存存储、关键词搜索、单进程锁。
- 区分单元测试、集成测试、模型行为 eval 和真实部署验收，不用其中一种代替其他类型。
- 逐条核对路径、导入和验证命令；命令注明工作目录及前置条件，避免从最终仓库复制尚未具备依赖的验收步骤。
- 保留“问题驱动演进”，同时允许前置设计安全边界与成功标准；拆模块依据职责和变化原因，不只依据行数。

## 官方参考

- [Commerce agents 博客](https://claude.com/blog/the-anatomy-of-effective-commerce-agents)：整体架构及生产实践原则。
- [Agent eval 指南](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)：尽早建立评估与持续回归。
- [Prompt caching 文档](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)：缓存前缀顺序、读写及失效行为。
