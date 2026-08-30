# 本地服务 AI 广告工厂

面向管道疏通等本地生活服务行业的一键 AI 广告生产系统。

## 产品目标

输入品牌、地区、服务项目、真实卖点和生成数量，系统自动完成：

1. Campaign Brain 选择广告策略与 AD DNA
2. Script Agent 生成广告脚本
3. Localizer Agent 生成地区化口语/方言版本
4. Director Agent 将脚本拆成逐镜头分镜
5. Asset Engine 优先匹配真实施工素材
6. Generation Engine 为缺失镜头调用 AI 图片/视频模型
7. Voice Engine 生成配音
8. Editing Engine 使用 FFmpeg 自动剪辑、字幕、BGM、Logo、CTA
9. QA Agent 检查字幕、品牌一致性、镜头匹配、重复度和不实承诺
10. Batch Engine 批量输出广告变体

## V1 聚焦行业

管道疏通：马桶、地漏、洗手池、厨房下水、下水道、主管道。

## 广告 DNA

每条广告由以下结构化维度生成：

- Hook：地域 / 痛点 / 紧急 / 时间 / 价格 / 好奇
- Customer Pain：堵塞 / 返水 / 排水慢等
- Customer Fear：乱收费 / 来得慢 / 修不好 / 不专业
- Service：马桶 / 地漏 / 洗手池 / 厨房 / 主管
- Selling Point：本地 / 快速 / 专业 / 设备 / 先检测 / 先报价
- Proof：真人师傅 / 施工现场 / 机器 / 前后对比 / 疏通结果
- Trust：价格透明 / 售后 / 企业认证 / 预约便利
- CTA：电话 / 私信 / 立即预约 / 平台预约

## 核心原则

- AI 不能自行编造商家承诺，只能使用 Business Profile 中确认过的 approved_claims。
- 真实施工、堵塞、设备和结果素材优先于 AI 生成素材。
- AI 视频主要补充缺失场景，例如上门、城市、住宅、夜间、预约等。
- LLM、TTS、图片和视频模型全部通过 Provider 接口接入，避免绑定单一供应商。
- 系统目标不是生成一条视频，而是持续生产低重复的广告矩阵。

## V1 开发顺序

Business Profile → Campaign Brain → AD DNA → Script Engine → Director Engine → Asset Library → Timeline → FFmpeg Renderer → Provider Interfaces → QA → Batch Generation

详细产品规格见 `docs/PRD.md`。
