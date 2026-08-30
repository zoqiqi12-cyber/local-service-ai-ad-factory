# 本地服务 AI 广告工厂 — V1 PRD

## 1. 产品定义

这不是传统视频编辑器，而是面向本地生活服务商家的 AI 广告生产流水线。用户不需要逐条写脚本、找镜头、配音和剪辑，只需配置商家资料和生成目标。

### 一键输入
- 品牌名称与 Logo
- 城市 / 区县 / 服务范围
- 服务项目
- 可验证的真实卖点
- 目标语言 / 地方化风格
- 视频时长
- 生成数量
- 真人素材目录

### 一键输出
- 广告策略
- 多版本脚本
- 地方化脚本
- 分镜表
- AI 生成缺失素材
- 配音
- 字幕
- 9:16 成片
- 标题与 CTA

## 2. 核心数据对象

### BusinessProfile
brand_name, industry, city, districts, services, approved_claims, forbidden_claims, booking_methods, brand_kit, languages.

### AdDNA
hook_type, pain, fear, service, selling_point, proof, trust, cta, creative_mode, target_duration.

### Script
hook, lines, CTA, title_candidates, language, locale, claims_used.

### ShotRequirement
line_id, semantic_intent, content_tags, required_objects, emotion, time_of_day, preferred_source, duration_range, generation_prompt.

### AssetShot
source_file, in/out, content_tags, semantic_tags, quality_score, hook_score, urgency_score, proof_score, result_score, used_count.

### Timeline
ordered clips, voice track, subtitles, music, overlays, brand elements and render settings.

## 3. 已归纳广告策略

A01 多业务关键词覆盖：地区 + 马桶/地漏/洗手池/下水道。

A02 附近快速上门：附近/同城/就近 + 服务 + 响应。

A03 本地口播：在{城市}，如果你家…… → 问题 → 解决方案 → CTA。

A04 紧急需求：严重堵塞/返水 → 紧迫感 → 快速响应 → 结果。

A05 搜索承接：本地服务词 → 联系/预约 → 就近响应。

A06 服务覆盖/时间：全城 + 服务时间 + 就近响应（仅允许使用商家确认的真实承诺）。

A07 痛点品牌利益：Pain → 情绪缓解 → Brand → Action → Proof → Benefit → CTA。

A08 价格信任：担心乱收费 → 检测 → 报价确认 → 施工 → 结果 → CTA。

A09 专业证明：问题 → 专业设备/师傅 → 施工过程 → 前后结果。

A10 品牌人物：固定师傅/口播人物 → 问题解释 → 服务能力 → CTA。

## 4. Campaign Brain

生成 N 条视频前先制定矩阵，而不是 N 次独立随机生成。控制广告策略占比、服务项目占比、Hook 多样性、人物/施工/AI素材比例，并参考历史生成记录降低重复度。

## 5. Script Engine

先生成结构化 AdDNA，再生成自然语言。脚本必须记录 claims_used 并逐项验证是否属于 approved_claims。禁止模型自动创造“24小时”“免费”“最低价”“30分钟到达”等未经商家确认的承诺。

## 6. Localizer

地方化不是机械替换城市名。流程：标准销售语义 → 当地自然口语改写 → 可选方言文本 → 对应 TTS。模型不支持的方言必须回退到普通话/当地口语，不伪造支持能力。

## 7. Director Engine

将每句脚本转换成 ShotRequirement。例：严重堵塞 → problem/urgent/severe；专业设备 → machine/professional/proof；疏通成功 → result/success/after。

## 8. 素材决策

优先级默认：真实高质量施工素材 > 已生成且质量合格的 AI 素材 > 新生成 AI 素材。

AI 适合补充：师傅出发、住宅外景、城市、夜间紧急场景、手机预约、过渡场景。真实素材优先用于堵塞、机器施工、污物清理、排水恢复等信任证明画面。

## 9. Provider 架构

定义统一接口：LLMProvider, TTSProvider, ImageProvider, VideoProvider。业务逻辑不得直接依赖某一家模型 API。Provider 负责 capability 声明、任务提交、轮询、下载、失败重试、费用记录。

## 10. Editing Engine

FFmpeg 为核心。V1 支持 9:16、1080x1920、配音驱动时间轴、字幕、Logo/水印、CTA、BGM ducking、基础硬切/轻转场、批量渲染。

## 11. QA

自动检查：空/黑帧、视频生成失败、字幕越界、字幕与配音时长、品牌名错误、禁止承诺词、镜头语义不匹配、重复镜头、同源素材过密、成片时长、音频峰值。

## 12. V1 UI

首页只保留完成任务所需字段：品牌项目、地区、服务、语言、广告策略（AI自动/手动）、真实素材开关、AI补镜头开关、时长、生成数量、一键生成。高级参数放二级页面。

## 13. V1 技术方案

Python 3.12；PySide6 桌面 UI；SQLite；FFmpeg/ffprobe；OpenCV 用于基础视觉分析；Pydantic 数据模型；Provider adapters 接外部 AI。

目录建议：

app/ui
app/models
app/database
app/campaign
app/script
app/localizer
app/director
app/assets
app/providers
app/editing
app/qa
app/jobs
app/utils

tests
configs
docs

## 14. 第一阶段验收标准

在没有任何外部 AI API 的情况下也能运行 Demo：创建 Business Profile → 从内置策略生成结构化 AdDNA → 用模板式 Mock LLM 生成脚本 → 自动生成 ShotRequirements → 导入本地视频 → 人工标签/基础切片 → 匹配素材 → 生成 timeline JSON。

第二阶段接入真实 LLM/TTS；第三阶段接 AI 视频；第四阶段实现自动 QA 和大批量任务队列。
