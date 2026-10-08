# OtherWise 宣传片：手工画面素材包

已按 2026-10-07 视频脚本制作 13 段独立视频，以及 AI 段落需要的 3 张透明标题叠层。

## 先看预览

- `OtherWise-manual-overview-52s.mp4`：52 秒风格速览，配 Quiet Horizons BGM，每段摘取 4 秒。
- `OtherWise-manual-scenes-preview.mp4`：2 分 19 秒手工部分顺序预览，配 BGM。
- 两个预览只包含本次制作的手工画面和真实产品操作，没有加入原有 AI 动画，也没有与旁白配音对齐。它们不是完整宣传片的最终剪辑。
- `OtherWise-manual-assets.zip`：可直接导入剪辑软件的素材包。

## 独立片段

所有 `clips/` 视频均为 1920×1080、30 fps、H.264、yuv420p，无音轨。底部 20% 留给字幕。编号对应原视频脚本，缺少的 01、02、05 是已经完成的 AI 场景。

| 文件 | 时长 | 画面内容 |
| --- | ---: | --- |
| `03-spotify.mp4` | 11 秒 | Spotify 论文卡片与“算法聆听 ↔ 消费多样性降低”关联 |
| `04-feedback-loop.mp4` | 12 秒 | 推荐内容 → 用户选择 → 训练数据的反馈循环 |
| `06-brand-meaning.mp4` | 12 秒 | Other / Wise / Think otherwise 品牌释义 |
| `07-choose-interest.mp4` | 9 秒 | 手动添加 Artificial intelligence，获取真实推荐 |
| `08-exploration-range.mp4` | 7 秒 | 实际调整 Outward range 参数 |
| `09-follow-a-topic.mp4` | 12 秒 | 搜索主题、保存兴趣，从新的起点获取推荐 |
| `10-interest-galaxy.mp4` | 10 秒 | 真实全屏地图与探索路径 |
| `11-auralist.mp4` | 16 秒 | Auralist 小样本研究，2.90 / 5.86 及可调新颖性的提议 |
| `12-purs.mp4` | 6 秒 | Unexpected + relevant 示意 |
| `13-contribution.mp4` | 13 秒 | 确认兴趣、渐进探索、可见路径的组合 |
| `14-research-question.mp4` | 15 秒 | 新发现能否发展为长期兴趣的研究问题 |
| `15-professor-invitation.mp4` | 10 秒 | 邀请教授指导的片尾前画面 |
| `16-end-card.mp4` | 6 秒 | 品牌、标语、项目网址和二维码 |

这些时长保留了阅读和剪辑余量，可在 ElevenLabs 时间线上裁短停留段。入场动画通常在前 1–4 秒完成；品牌释义依次出现至约第 8 秒，Auralist 的 novelty 提议在第 9 秒后出现。剪短时保留这些内容的入场时间。

## 透明标题与可编辑画面

`layers/` 内含各手工场景的独立 PNG 图层及背景，可以修改或重新排版。

以下透明 PNG 可直接叠加在已经完成的 AI 视频上，均为 1920×1080：

- `01-ai-caption-transparent.png`：Something new?
- `02-ai-caption-transparent.png`：What are we missing?
- `05-ai-caption-transparent.png`：Make room for new interests.

`stills/` 是所有 13 个片段的完整静帧，可作为备选静态素材。

## 产品操作来源

产品部分使用当前 OtherWise 扩展源码、独立临时浏览器配置，以及本机真实 MPNet 推荐服务拍摄。没有使用虚构的推荐结果或绘制的模拟界面。界面通过真实操作连续截图记录，随后编码为视频，剪掉了等待服务返回的空档，并适当放慢动作、停留在真实末帧以便观看。

拍摄起点为 Artificial intelligence；调整探索范围后，实际结果中的 Turing Award 被搜索并保存，再从该兴趣继续请求推荐。地图上的连线来自这些实际操作。

## 研究信息

- [Anderson et al., WWW 2020](https://doi.org/10.1145/3366423.3380281)：画面明确标注 observed association，消费多样性不等同于长期兴趣变化的证明。
- [Chaney et al., RecSys 2018](https://doi.org/10.1145/3240323.3240370)：反馈循环的同质化与效用下降标注为 simulation study。
- [Zhang et al., WSDM 2012](https://doi.org/10.1145/2124295.2124300)：2.90 与 5.86 为 20 项推荐列表中被喜欢、此前不熟悉的艺术家数；n = 21。可调新颖性属于作者提议。
- [Li et al., PURS, RecSys 2020](https://doi.org/10.1145/3383313.3412238)：画面为意外性与相关性的设计示意，不是 OtherWise 的实验结果。

## 片尾与核对

项目网址：https://roboticreaper.github.io/OtherWise/

网站已在 Chrome 打开并核对；二维码已通过本机条码识别读取并核对网址。所有视频已核对分辨率、帧率、时长和解码，并抽帧检查版面。

ElevenLabs 项目：https://elevenlabs.io/app/studio/F7kcOV2voz0vs5guJ2Br

云端上传未完成：网页上传按钮未能打开浏览器工具可用的文件选择器。可将素材包中的 `clips/` MP4 和透明标题 PNG 手动导入该项目素材库，再按旁白时间点排列。
