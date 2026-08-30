# 本地服务 AI 广告工厂

面向管道疏通等本地生活服务行业的一键 AI 广告生产系统。

## 产品目标

输入品牌、地区、服务项目、真实卖点和生成数量，系统自动完成：

1. Campaign Brain 选择广告策略与 AD DNA
2. Script Agent 生成广告脚本
3. Localizer Agent 生成地区化口语/方言版本
4. Director Agent 将脚本拆成逐镜头分镜
5. Asset Engine 自动切镜头、理解真实施工素材并优先匹配
6. Generation Engine 为缺失镜头调用 AI 视频模型
7. Voice Engine 生成配音
8. Editing Engine 使用 FFmpeg 自动剪辑、字幕、BGM、Logo、CTA
9. QA Agent 检查字幕、品牌一致性、镜头匹配、重复度和不实承诺
10. Batch Engine 批量输出广告变体，并通过 Campaign History 降低重复

## 当前 V1 已实现

- Business Profile / approved claims 安全约束
- 10 类广告策略与 Campaign Brain
- Campaign History：记录广告 DNA / 脚本 / 素材使用，下一批主动避重
- 模板 Script Engine + 可选 LLM Script Agent；LLM 失败自动回退本地模板
- LLM 输出强制结构化，并再次过滤未授权卖点和禁用宣传词
- 地方化 Localizer
- Script → ShotRequirements 的 Director Engine
- 快切 / 真人施工 / 混合等创意模式与多镜头节奏
- FFmpeg 场景切分：一条长素材自动拆成 shot
- 文件名/目录名的启发式标签
- 清晰度、运动强度、稳定性、画质分析
- 感知视觉指纹与相似镜头去重
- 可选 Vision Provider：真正看关键帧识别马桶、地漏、污水、师傅、机器、施工、排水成功等
- Hook 阶段偏向高运动/高紧迫镜头；结果阶段偏向稳定清晰镜头
- 真实素材匹配与 AI 缺失镜头标记
- LLM / Vision / AI Video / TTS Provider 可插拔接口
- AI pending 镜头生成后自动回填 timeline
- SRT 字幕生成
- FFmpeg 9:16 基础渲染
- 配音 + BGM + 烧录字幕的 Final Composer
- 一条广告从计划到最终 MP4 的 Execution Engine
- 批量成片 Batch Execution Engine
- QA：未授权承诺、AI 未完成、时间轴、重复镜头等
- PySide6 桌面 UI，已接到计划、素材分析和成片执行
- App 内“AI服务设置”：可直接填写 LLM / Vision / TTS / AI Video 地址与 API Key
- API Key 仅保存在本机用户目录，不需要提交 GitHub；环境变量仍可覆盖本地设置
- Windows 一键启动脚本 + 环境 Doctor
- Windows PyInstaller 打包工作流
- pytest + GitHub Actions 自动测试

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
- LLM、Vision、TTS、图片和视频模型全部通过 Provider 接口接入，避免绑定单一供应商。
- 系统目标不是生成一条视频，而是持续生产低重复的广告矩阵。

## Windows 最简单运行方式

需要先安装 Python 3.12+。FFmpeg 需要在系统 PATH 中。

第一次：双击 `run_windows.bat`，它会自动创建 `.venv` 并安装项目。之后继续双击同一个文件即可打开桌面 App。

打开 App 后，点 **AI服务设置**，即可填写脚本大模型、视觉模型、配音和 AI 视频服务的地址/API Key。设置保存在：

```text
%USERPROFILE%\.local_service_ai_ad_factory\settings.json
```

如果启动有问题，可在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m app.doctor
```

## 通用本地运行

```bash
pip install -e .
python -m app.main
```

命令行只生成广告计划：

```bash
python -m app.cli --city 中山市 --count 5 --language 中山口语
```

没有配置外部 AI Provider 时，系统仍可完成脚本、分镜、真实素材切分、基础标签、视觉评分、素材匹配和 timeline；只有确实缺失的镜头会保持 `ai_pending`，不会伪造成已经生成。

## 接 LLM / Vision / AI 视频 / TTS

桌面用户优先直接使用 App 内的 **AI服务设置**。服务器或高级用户仍可使用环境变量，参考 `.env.example`；环境变量优先级高于本地设置。

```bash
export AD_FACTORY_LLM_URL="https://your-gateway.example/llm"
export AD_FACTORY_LLM_API_KEY="..."

export AD_FACTORY_VISION_ENDPOINT="https://your-gateway.example/vision"
export AD_FACTORY_VISION_API_KEY="..."

export AD_FACTORY_TTS_ENDPOINT="https://your-gateway.example/tts"
export AD_FACTORY_TTS_API_KEY="..."
export AD_FACTORY_TTS_LANGUAGES="普通话"
export AD_FACTORY_TTS_DIALECTS="粤语,中山口语"

export AD_FACTORY_VIDEO_ENDPOINT="https://your-gateway.example/video"
export AD_FACTORY_VIDEO_API_KEY="..."
export AD_FACTORY_VIDEO_MAX_SECONDS="10"
```

LLM 网关接收：`system_prompt / user_prompt / schema`，返回 JSON object，或 `{ "result": {...} }`。

Vision 网关接收：`image_base64 / prompt / schema`，返回镜头标签和广告语义评分 JSON；未知标签会被白名单过滤。

TTS 网关接收：`text / language / output_format`，返回音频二进制，或 JSON 中的 `file_url/audio_url/url`。

AI Video 网关接收：`prompt / duration / aspect_ratio / output_format`，返回视频二进制，或 JSON 中的 `file_url/video_url/url`。

这样后续接任意实际模型时，只做一个薄适配层，不重写广告业务逻辑。

详细产品规格见 `docs/PRD.md`。
