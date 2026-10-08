# OtherWise 的学术依据：推荐反馈、内容多样性与兴趣探索

研究日期：2026-10-05（美国中部时间）。整理 **19 篇英文原始论文**：10 篇风险、机制与反证，9 篇方案或兴趣发展理论。优先采用正式会议、期刊、作者及大学公开版本；这是针对项目的文献检索，不是穷尽性系统综述。“已读全文”指已访问正文并核对相关方法、结果与局限，未必逐页阅读所有附录；仅读摘要和公开稿的情况另有注明。

## 可以成立的项目出发点

**有些推荐方式会让用户实际接触或消费的内容更集中；仅优化当前偏好或短期参与度，也可能留下探索不足的问题。但现有证据不足以说明所有推荐算法都会缩窄人的真实兴趣，更不能说明增加内容多样性就一定降低政治极化。** Spotify 的随机实验与音乐观察研究提供了与日常兴趣探索比较接近的依据；MovieLens 的结果则说明推荐也可能减轻内容收窄。[Holtz 等，完整研究稿](https://ide.mit.edu/wp-content/uploads/2020/03/SSRN-id3555927.pdf)、[Anderson 等，WWW 2020](https://www.cs.toronto.ca/~ashton/pubs/alg-effects-spotify-www2020.pdf)、[Nguyen 等，WWW 2014](https://archives.iw3c2.org/www2014/proceedings/proceedings/p677.pdf)。

OtherWise 更稳妥的定位是：**帮助用户主动发现当前兴趣以外、又仍有一定关联的新话题，并让用户控制探索的范围。** 当前 [README](../../README.md) 描述的是语义距离范围与结果多样性；语义距离不能直接证明心理兴趣、观点差异、长期学习效果或去极化效果。这些应是未来评估的问题。

## 必须区分的四个概念

| 概念 | 研究实际测量什么 | 对 OtherWise 的含义 |
|---|---|---|
| 推荐/曝光多样性 | 系统展示了多少不同类别、来源或语义内容 | 可以在系统层面直接测试 |
| 消费多样性 | 用户点击、播放、评分的内容分布 | 必须观察真实使用；展示不等于消费 |
| 心理兴趣广度 | 用户是否产生并维持新的兴趣 | 不能只用点击或 embedding 距离代替 |
| 政治态度/极化 | 对政策、政党或对立群体的调查指标 | 与话题新颖性是不同结果，不能互相代替 |

前两项在 Spotify、MovieLens 与 Facebook 研究中有不同操作化方式；后两项不能从它们自动推导。Chaney 的模拟甚至把潜在偏好设为固定，研究的是行为同质化；Jiang 才在假设模型中让兴趣随交互改变。[Chaney 全文，§4–5](https://arxiv.org/pdf/1710.11214)、[Jiang 全文，Model 与 System Design Role](https://www.aies-conference.com/2019/wp-content/papers/main/AIES-19_paper_187.pdf)。

## 证据强度与优先阅读顺序

下表的“强”指在该研究设置中辨认因果效果的能力，不代表能直接证明 OtherWise 的效果。

| 论文 | 设计/来源 | 可支持的核心论点 | 主要边界 | 阅读情况 |
|---|---|---|---|---|
| [Holtz et al., 2020](https://doi.org/10.1145/3391403.3399532) | Spotify 大规模随机实验；ACM EC 会议短论文与完整研究稿 | 个性化、参与度与多样性之间存在具体权衡 | 个体 −11.51% 是处理后条件比较；不能直接称因果 | 完整研究稿正文、§5 与附录 D/G |
| [Anderson et al., 2020](https://doi.org/10.1145/3366423.3380281) | Spotify 大规模观察＋单独随机排序实验；WWW | 推荐消费与较低音乐多样性相关 | 观察关联不是“推荐导致收窄”；随机实验测试短期排序效果 | 全文相关方法/结果 |
| [Nguyen et al., 2014](https://doi.org/10.1145/2566486.2568012) | MovieLens 纵向日志；WWW | 整体略收窄，但采纳推荐者收窄更少 | 非随机；“采纳”由日志推断 | 全文方法与讨论 |
| [Chaney et al., 2018](https://doi.org/10.1145/3240323.3240370) | 多类推荐算法模拟；ACM RecSys | 被历史推荐影响的数据可产生自强化反馈 | 模拟、固定潜在偏好 | 全文方法/结果 |
| [Jiang et al., 2019](https://doi.org/10.1145/3306618.3314288) | 理论＋模拟；AAAI/ACM AIES | 特定兴趣动态下的退化条件与探索作用 | 条件模型，不是真人兴趣变化证据 | 全文模型/设计结论 |
| [Bakshy et al., 2015](https://doi.org/10.1126/science.aaa1160) | Facebook 观察数据；Science | 网络、排序与用户选择共同塑造曝光 | 非随机；不能只归因于算法 | 全文正文 |
| [Nyhan et al., 2023](https://doi.org/10.1038/s41586-023-06297-w) | Facebook 随机干预；Nature | 同阵营来源曝光明显下降，态度未可测改变 | 美国2020选举、三个月、特定降权措施 | 当前更新后的开放正文 |
| [Guess et al., 2023](https://doi.org/10.1126/science.abp9364) | Facebook/Instagram 随机换 feed；Science | 体验/曝光改变不必伴随态度变化 | 本次仅读机构摘要；存在两次勘误 | 原始机构摘要；全文访问失败 |
| [Gauthier et al., 2026](https://doi.org/10.1038/s41586-026-10098-2) | X 随机换 feed；Nature | 特定切换方向可改变政策/时事态度 | 无显著情感极化变化；方向不对称 | 开放全文设计/结果/讨论 |
| [Bail et al., 2018](https://doi.org/10.1073/pnas.1804840115) | Twitter 随机鼓励关注对立观点 bot；PNAS | 对立观点曝光不保证降低极化 | 美国高频、明确党派用户及精英消息 | 正文与研究设计/局限 |

## 注释书目：风险、机制与反证

### 1. 最接近日常兴趣内容的随机证据：Spotify 播客

**The Engagement-Diversity Connection: Evidence from a Field Experiment on Spotify** — David Holtz, Benjamin Carterette, Praveen Chandar, Zahra Nazari, Henriette Cramer, Sinan Aral. 2020. *Proceedings of the 21st ACM Conference on Economics and Computation*, 75–76. [会议 DOI](https://doi.org/10.1145/3391403.3399532)；[MIT 最终版本记录](https://dspace.mit.edu/entities/publication/44770084-3b9f-44fa-a665-8958c684d3dc)；[已读完整研究稿](https://ide.mit.edu/wp-content/uploads/2020/03/SSRN-id3555927.pdf)（数值与方法来自该稿，不能把两页会议版本称作长篇期刊论文）。

- **设计与发现：**852,937 位此前未在 Spotify 播放/关注播客的 Premium 用户，17 国、两周；音乐历史个性化推荐对照同人口组热门播客。播客播放量增加 28.90%；至少播放一次的人群中，类别 Shannon 熵低 11.51%；各用户消费分布之间的差异（文中的 intragroup diversity）增加 5.96%。[完整稿，§4–5](https://ide.mit.edu/wp-content/uploads/2020/03/SSRN-id3555927.pdf)。
- **关键因果限制：**−11.51% 条件于处理后的“是否收听”，作者明确说不能解释成用户层面因果效应。全样本平均熵因更多人开始收听而增加；主分层估计对“无论分组都会收听者”得到熵下降 0.070，依赖该分析的识别假设。附录 D 的效果在实验结束后迅速缩小或消失。[完整稿，§5.2、附录 D/F/G](https://ide.mit.edu/wp-content/uploads/2020/03/SSRN-id3555927.pdf)。
- **OtherWise 用法：**支持分别评估个体探索、群体差异与参与度；不能写“随机实验证明每个人兴趣缩窄 11.51%”，也没有测心理兴趣或极化。

### 2. Spotify 音乐：关联证据与短期推荐益处并存

**Algorithmic Effects on the Diversity of Consumption on Spotify** — Ashton Anderson, Lucas Maystre, Rishabh Mehrotra, Ian Anderson, Mounia Lalmas. 2020. *The Web Conference (WWW)*. [DOI](https://doi.org/10.1145/3366423.3380281)；[作者大学全文](https://www.cs.toronto.ca/~ashton/pubs/alg-effects-spotify-www2020.pdf)。已读正文的测量、纵向分析与实验结果。

- **发现：**用歌曲行为 embedding 测消费相似性，算法驱动播放与较低多样性相关；提高消费多样性的用户也更偏向自主播放。较高多样性与留存/付费转化相关。另有 540,000 名免费用户的一周随机排序实验，相关性排序比热门排序带来更多播放，尤其对原本较专一的用户。[全文，§3–6](https://www.cs.toronto.ca/~ashton/pubs/alg-effects-spotify-www2020.pdf)。
- **不能推出：**随机实验的播放/跳过指标没有证明算法造成长期多样性下降；留存关联也不是“多样性提高会导致留存提高”，播放量只是体验代理指标。
- **OtherWise 用法：**合理保留相关性，同时加入多样性目标；不能据此声称 OtherWise 提高满意度或长期留存。

### 3. 必须纳入的反证：MovieLens 推荐可能减轻收窄

**Exploring the Filter Bubble: The Effect of Using Recommender Systems on Content Diversity** — Tien T. Nguyen, Pik-Mai Hui, F. Maxwell Harper, Loren Terveen, Joseph A. Konstan. 2014. *WWW*, 677–686. [DOI](https://doi.org/10.1145/2566486.2568012)；[官方会议全文](https://archives.iw3c2.org/www2014/proceedings/proceedings/p677.pdf)。已读方法、结果与讨论。

- **设计与发现：**1,405 名 MovieLens 用户的长期评分/推荐日志，使用 tag genome 衡量内容差异。推荐和被评分电影总体随时间略收窄；但会评分系统推荐电影的人，收窄更小，且对推荐电影评分更正面。[全文，§3–5](https://archives.iw3c2.org/www2014/proceedings/proceedings/p677.pdf)。
- **不能推出：**没有随机分派“采纳推荐”；日志也不能确认电影消费受哪一个推荐源影响。电影、item-item 协同过滤结果不能推广到全部平台。
- **OtherWise 用法：**项目应论证“增加自主探索的选择”，不必把普通推荐系统全部当作问题来源。

### 4. 自强化机制：历史推荐会影响训练数据

**How Algorithmic Confounding in Recommendation Systems Increases Homogeneity and Decreases Utility** — Allison J. B. Chaney, Brandon M. Stewart, Barbara E. Engelhardt. 2018. *ACM RecSys*, 224–232. [DOI](https://doi.org/10.1145/3240323.3240370)；[作者 arXiv 全文](https://arxiv.org/pdf/1710.11214)。已读模型、模拟与结果。

- **发现：**比较内容过滤、矩阵分解、社交、热门等推荐模拟；在被先前推荐影响的数据上反复训练，会强化用户消费行为同质化，且不必带来相应效用增加，部分用户效用受损。[全文，§4–5](https://arxiv.org/pdf/1710.11214)。
- **不能推出：**模型的潜在偏好近似固定；因此论文不是“真人的兴趣被改变”的实证。行为同质化指用户消费集合更相似，也不等于某个用户的主题范围必然更窄。
- **OtherWise 用法：**为探索、覆盖与多样性评价提供机制动机；当前项目并没有这类持续训练反馈回路，不能声称已修复论文的问题。

### 5. 理论上为何“更准确”未必解决探索问题

**Degenerate Feedback Loops in Recommender Systems** — Ray Jiang, Silvia Chiappa, Tor Lattimore, András György, Pushmeet Kohli. 2019. *AAAI/ACM Conference on AI, Ethics, and Society (AIES)*, 383–390. [DOI](https://doi.org/10.1145/3306618.3314288)；[官方会议全文](https://www.aies-conference.com/2019/wp-content/papers/main/AIES-19_paper_187.pdf)。已读兴趣动态模型、系统设计与模拟结论。

- **发现：**在特定自强化兴趣动态下，准确预测配合贪心推荐可能加快兴趣变量向极端发展的速度。探索程度及候选集增长会影响退化；模拟中持续探索和增长候选集可减缓某些退化。[全文，Model、System Design Role、Simulation Experiments](https://www.aies-conference.com/2019/wp-content/papers/main/AIES-19_paper_187.pdf)。
- **不能推出：**这是定理和模拟的条件结论；“兴趣”是模型变量，不是心理量表；有限候选集下加随机性也不保证消除退化。
- **OtherWise 用法：**支持研究探索策略，不能直接拿本文为固定目录、固定距离带的产品效果背书。

### 6. 信息曝光不只由算法决定：Facebook 新闻

**Exposure to ideologically diverse news and opinion on Facebook** — Eytan Bakshy, Solomon Messing, Lada A. Adamic. 2015. *Science* 348(6239), 1130–1132. [DOI](https://doi.org/10.1126/science.aaa1160)；[大学托管正文](https://education.biu.ac.il/files/education/shared/science-2015-bakshy-1130-2.pdf)。已读正文。

- **设计与发现：**10.1 百万自报政治倾向的活跃美国用户；将朋友可能分享、实际排序曝光及点击分开。朋友网络构成、排序与用户点击选择都限制跨政治阵营信息接触，作者强调个人选择的重要性。[正文，Fig.3 与讨论](https://education.biu.ac.il/files/education/shared/science-2015-bakshy-1130-2.pdf)。
- **不能推出：**观察性研究，非随机算法开关；样本不是所有美国人，点击也不能覆盖只读摘要的曝光；没有测推荐造成的态度改变。
- **OtherWise 用法：**用户主动控制与选择可能是重要设计维度；但“用户控制有效改变长期习惯”仍需单独实验。

### 7. 强反证：减少同阵营曝光未可测地降低极化

**Like-minded sources on Facebook are prevalent but not polarizing** — Brendan Nyhan, Jaime Settle, Emily Thorson, Magdalena Wojcieszak, et al. 2023. *Nature* 620, 137–144. [DOI与开放全文](https://www.nature.com/articles/s41586-023-06297-w)。已读当前更新正文的实验方法、结果和讨论；出版页面标有2023年作者更正，本记录未单独核实更正内容。

- **发现：**美国2020选举期间，23,377 人的三个月实验把同阵营来源曝光减少约三分之一；跨阵营来源曝光增加，不文明内容及反复传播错误信息的来源曝光减少，但八项预注册态度指标没有可测变化，包括情感极化、意识形态极端程度等。[全文，Experimental effects 与 Discussion](https://www.nature.com/articles/s41586-023-06297-w)。
- **不能推出：**实验不能证明算法在其他平台、国家、年龄或更长期没有影响；“同阵营来源”也不等于每篇内容自身的立场。
- **OtherWise 用法：**多样化曝光可能是独立目标；不能以曝光改变替代政治改善，更不能宣称 OtherWise 去极化。

### 8. 补充反证，但本次全文与勘误核对受限

**How do social media feed algorithms affect attitudes and behavior in an election campaign?** — Andrew M. Guess, Neil Malhotra, Jennifer Pan, Pablo Barberá, et al. 2023. *Science* 381(6656), 398–404. [DOI](https://doi.org/10.1126/science.abp9364)；[作者机构原始摘要与全文入口](https://www.networkscienceinstitute.org/publications/how-do-social-media-feed-algorithms-affect-attitudes-and-behavior-in-an-election-campaign)。**本次只成功读取原始机构摘要，Science 全文访问失败。**

- **摘要支持的结论：**2020选举期间随机将 Facebook/Instagram 用户切换为逆时序 feed，平台使用与内容曝光明显改变；三个月内政治知识、议题/情感极化等没有显著变化。[作者机构摘要](https://www.networkscienceinstitute.org/publications/how-do-social-media-feed-algorithms-affect-attitudes-and-behavior-in-an-election-campaign)。
- **版本限制：**[Crossmark 更新记录](https://crossmark.crossref.org/dialog-content?date_stamp=2023-07-27&doi=10.1126%2Fscience.abp9364&domain=pdf)列出2024年 [10.1126/science.adu8261](https://doi.org/10.1126/science.adu8261) 与2026年 [10.1126/science.aeh2575](https://doi.org/10.1126/science.aeh2575) 两次更正，本次未获取更正正文。正式稿若使用细节/数值，应先查更新正文；不能据旧摘要作“算法总会放大错误信息”的结论。
- **OtherWise 用法：**作为区分曝光与态度的补充，优先以已读完整的 Nyhan 为证据。

### 9. 新的因果证据：算法可改变部分态度，关闭却不一定逆转

**The political effects of X’s feed algorithm** — Germain Gauthier, Roland Hodler, Philine Widmer, Ekaterina Zhuravskaya. 2026. *Nature* 652, 416–423（线上发表2026-02-18）. [DOI与开放全文](https://www.nature.com/articles/s41586-026-10098-2)。已读设计、主要结果与讨论。

- **设计与发现：**2023年美国 X 用户七周实验，主样本4,965人。原本用时序 feed 的人随机改用算法 feed 后，若干政策/时事态度向保守方向移动，也更可能关注保守账号；原本用算法 feed 的人改用时序 feed，没有对应态度变化。两个方向均未显著改变情感极化或自报党派归属。[全文，Design 与 Impact of feed algorithm](https://www.nature.com/articles/s41586-026-10098-2)。
- **不能推出：**具体立场变化不等同于极化增加，也不等同于错误信息信念；初始使用不同 feed 的用户不是随机形成的，作者承认未观察差异可能解释部分不对称性。
- **OtherWise 用法：**说明算法可以改变一些结果，也说明只“关闭个性化”不一定逆转历史路径；不能推广为所有推荐算法的长期心理伤害。

### 10. 设计边界：直接推送对立观点可能适得其反

**Exposure to opposing views on social media can increase political polarization** — Christopher A. Bail, Lisa P. Argyle, Taylor W. Brown, et al. 2018. *PNAS* 115(37), 9216–9221. [DOI](https://doi.org/10.1073/pnas.1804840115)；[大学托管全文与附录](https://dlab.epfl.ch/teaching/spring2019/cs718/papers/bail2018exposure.pdf)。已读正文的研究设计、结果与局限。

- **设计与发现：**随机向高频使用 Twitter 的美国民主/共和党认同者提供报酬，鼓励关注一个月转发对立阵营精英消息的 bot。共和党处理组更保守，民主党组的小幅更自由没有显著性。[正文，Research Design 与 Results](https://dlab.epfl.ch/teaching/spring2019/cs718/papers/bail2018exposure.pdf)。
- **不能推出：**并非推荐算法对照实验；政治精英消息、经济鼓励与明确党派高频用户场景，不能代表所有跨观点接触或日常兴趣探索；反作用的具体机制也未被确定。
- **OtherWise 用法：**“新颖”不应被定义成“越对立越好”；由用户控制相关但陌生话题的探索，是合理设计假设，效果仍需评估。

## 如何表达“其他负面影响”

可以写“特定模型中用户效用下降”（Chaney），或“某些真实平台算法能影响具体政治态度”（Gauthier）；必须带上模拟/平台/时间与结果类型。[Chaney](https://arxiv.org/pdf/1710.11214)、[Gauthier](https://www.nature.com/articles/s41586-026-10098-2)。

目前这些论文不支持把 OtherWise 宣传成防止成瘾、减少焦虑、提高创造力、纠正错误信息或降低极化的有效干预。Anderson 的留存/转化是关联和平台指标，Jiang 的兴趣退化是模型概念，不能冒充心理健康结果。[Anderson](https://www.cs.toronto.ca/~ashton/pubs/alg-effects-spotify-www2020.pdf)、[Jiang](https://www.aies-conference.com/2019/wp-content/papers/main/AIES-19_paper_187.pdf)。

## 研究者提出的方案：与 OtherWise 最接近的先例

**最有用的组合是 PURS 的适中意外性、Auralist 的探索程度控制，以及交互式可视化的用户主导。** 这些论文为设计选择提供依据；它们测试的模型、内容与界面不同，不能把其效果直接移植为 OtherWise 的效果。[PURS 正文 §3](https://arxiv.org/pdf/2106.02771)、[Auralist 正文 §6–7](https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf)、[交互式可视化正文 §3–4](https://julita.usask.ca/Texte/ht84nagulendra.pdf)。

| 研究方向 | 主要论文 | 与 OtherWise 的对应（本报告的比较判断） | 证据边界 |
|---|---|---|---|
| 多个兴趣区域、适中的意外性 | PURS，RecSys 2020 | 用 embedding 表示多个兴趣，从相关但陌生的内容中发现新方向 | 论文用学习到的簇与加权距离；我们用最近兴趣距离及硬距离带，算法不同 |
| 用户调节探索程度 | Auralist，WSDM 2012 | Close / Balanced / Broader，以及探索范围控制 | 调节控件是论文提出的设计建议；实验并未检验我们的参数 |
| 让用户看懂并改变筛选 | Nagulendra & Vassileva，HT 2014 | 可解释推荐、可编辑兴趣、探索地图 | 主要支持短期理解与控制；没有证明长期兴趣扩展 |
| 帮陌生内容变得有意义 | Binst et al.，UMAP 2026 | 不只给一个新主题，还解释它为什么值得探索 | 测音乐介绍与当下体验；不是跨学科长期兴趣实验 |
| 降低推荐列表重复 | MMR，SIGIR 1998 | 在范围约束后加入结果间相似性惩罚 | 是排序方法依据，不是心理兴趣或去极化证据 |

### 11. PURS：技术结构最接近我们的一篇

**PURS: Personalized Unexpected Recommender System for Improving User Satisfaction** — Pan Li, Maofei Que, Zhichao Jiang, Yao Hu, Alexander Tuzhilin. 2020. *ACM RecSys*. [DOI](https://doi.org/10.1145/3383313.3412238)；[作者公开全文](https://arxiv.org/pdf/2106.02771)（2021 年上传，正文明确是 RecSys 2020 论文）。已核对 §3、§7 和结果表。

- **方案与证据：**把既有兴趣分为多个 embedding 簇，用候选内容到这些簇的距离表示意外性，并以单峰函数避免一味选择最远、最不相关的项目。包含离线比较及优酷在线 A/B 测试；报告人均视频播放 +3.74%、意外性指标 +9.74%。[全文，§3、Table 4](https://arxiv.org/pdf/2106.02771)。
- **对应与限制：**为“多个兴趣区域＋适中陌生程度”提供直接技术先例。论文仍结合点击预测；这些平台指标没有证明长期兴趣更广，也没有直接测量标题中所说的心理满意度。我们的距离带、最近兴趣规则与其算法不同。

### 12. Auralist：明确建议让用户控制探索程度

**Auralist: Introducing Serendipity into Music Recommendation** — Yuan Cao Zhang, Diarmuid Ó Séaghdha, Daniele Quercia, Tamas Jambor. 2012. *ACM WSDM*, 13–22. [DOI](https://doi.org/10.1145/2124295.2124300)；[大学托管全文](https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf)。已核对 §6–7。

- **方案与证据：**平衡准确性、多样性、新颖性与 serendipity。21 人短期用户研究中，完整版带来更多有用的新发现，但平均单项喜爱评分下降；12 人偏好完整版，7 人偏好更贴近已有口味的基线，2 人中立。[全文，Table 3、§6–7](https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf)。
- **对应与限制：**作者据这种偏好差异，明确提出让用户通过不同列表或滑动控制调节推荐的探索程度。很适合支持我们的范围控制；这是设计建议，小样本实验未证明持续兴趣变化。

### 13. 可视化与控制：与 Galaxy 理念接近

**Understanding and Controlling the Filter Bubble through Interactive Visualization: A User Study** — Sayooran Nagulendra, Julita Vassileva. 2014. *ACM Hypertext and Social Media (HT)*, 107–115. [DOI](https://doi.org/10.1145/2631775.2631811)；[作者大学全文](https://julita.usask.ca/Texte/ht84nagulendra.pdf)。已核对界面设计、实验与结论。

- **方案与证据：**把显示和隐藏的社交内容来源可视化，让用户直接调整过滤。163 份有效众包回应显示参与者能理解不少界面功能及其控制作用。[全文，§3–4](https://julita.usask.ca/Texte/ht84nagulendra.pdf)。
- **对应与限制：**支持“让用户看懂并主导探索”。研究使用介绍、模拟内容和单组理解测试，不能据此宣称可视化因果性地拓宽长期兴趣。该系统显示真实被隐藏的内容；OtherWise 的 Galaxy 展示自己的主题与路径，不能声称揭示了 YouTube 等平台隐藏的推荐。

### 14. 新的用户实验：介绍陌生内容有助于触发兴趣

**Let Me Introduce You: Stimulating Taste-Broadening Serendipity through Song Introductions** — Brett Binst, Ulysse Maes, Martijn C. Willemsen, Annelien Smets. 2026. *ACM UMAP*, 127–136. [DOI](https://doi.org/10.1145/3774935.3806164)；[官方会议程序](https://www.um.org/umap2026/program/)；[作者公开全文](https://arxiv.org/html/2604.08385v1)。发表状态由会程确认，方法与数值依据公开稿；未比对出版终稿的每项细节。

- **方案与证据：**350 名符合陌生音乐条件的参与者，在有不同介绍或无介绍时听歌曲。报告 taste-broadening serendipity 的比例，无介绍为 38.4%，信息介绍为 55.9%；效果因歌曲和介绍质量而异。[全文，§3.3、§4.1](https://arxiv.org/html/2604.08385v1)。
- **对应与限制：**提示 OtherWise 可研究有内容的解释如何帮助新主题变得有意义。实验测当下体验和继续探索意愿；不能把这些比例当成长期兴趣形成率，也不能把音乐介绍效果直接推广到简短主题卡片。

### 15. MMR：多样性排序的经典依据

**The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries** — Jaime Carbonell, Jade Goldstein. 1998. *ACM SIGIR*, 335–336. [DOI](https://doi.org/10.1145/290941.291025)；[作者大学全文](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf)。已核对两页正文。

MMR 在相关性和与已选结果的重复程度之间做可调权衡。OtherWise 的逐项选择也对结果间相似性施加惩罚，属于相近的排序思路；我们的基础分数来自距离带中点匹配，不能称为完整复现 MMR。论文的人类检索试验只有五人，主要贡献是方法。[原文，§2–3](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf)。

### 16. 适中的陌生程度：早期效用模型

**On Unexpectedness in Recommender Systems: Or How to Expect the Unexpected** — Panagiotis Adamopoulos, Alexander Tuzhilin. 2011. *DiveRS workshop at ACM RecSys*, CEUR-WS Vol. 816, 11–18. [官方书目](https://ceur-ws.org/Vol-816/)；[论文全文](https://ceur-ws.org/Vol-816/paper2.pdf)。已核对 §3–5。

论文把质量与偏离用户预期的程度一起建模，假设每个用户与情境存在偏好的意外程度，过于熟悉或偏离过远都可能降低效用；在电影数据上做离线比较。这为探索范围提供理论思路，不能当成人类普遍存在某个固定最佳语义距离的证明。[原文，§3.2、§4–5](https://ceur-ws.org/Vol-816/paper2.pdf)。本报告使用实际读到的 2011 年工作坊版本，不混用后续期刊版本的细节。

### 17. Serendipity 需要用户体验，不能只看距离

**What Is Serendipity? An Interview Study to Conceptualize Experienced Serendipity in Recommender Systems** — Brett Binst, Lien Michiels, Annelien Smets. 2025. *ACM UMAP*, 243–252. [DOI](https://doi.org/10.1145/3699682.3728325)；[研究机构托管终稿](https://imec-publications.be/server/api/core/bitstreams/d53afde9-0a02-4872-a8bf-5861c0e69281/content)。已核对方法与概念框架；亦查看作者 arXiv 版本。

17 人访谈提出：偶遇体验需要意外发现、新鲜感及对本人有价值等要素。可用它设计用户访谈，判断 OtherWise 是否带来有意义的发现。它是小样本形成的概念框架，不是“语义距离高＝serendipity 高”的定律，也没有测试我们的产品。[终稿，§3–4](https://imec-publications.be/server/api/core/bitstreams/d53afde9-0a02-4872-a8bf-5861c0e69281/content)。

### 18. 兴趣发展：为什么一次点击还不够

**The Four-Phase Model of Interest Development** — Suzanne Hidi, K. Ann Renninger. 2006. *Educational Psychologist* 41(2), 111–127. [DOI](https://doi.org/10.1207/s15326985ep4102_4)；[作者大学书目与摘要](https://works.swarthmore.edu/fac-education/12/)。本次核对作者机构摘要，机构页面不提供全文，未把它当作已读全文。

该理论区分情境兴趣被触发、情境兴趣被维持，以及个人兴趣的形成和深化。它为 OtherWise 区分“看见新内容”“短暂觉得有趣”和“愿意持续参与”提供理论框架；没有证明浏览器推荐会使真实兴趣变窄或变广。[作者机构摘要](https://works.swarthmore.edu/fac-education/12/)。

### 19. TasteWeights：解释、编辑画像与实时控制

**TasteWeights: A Visual Interactive Hybrid Recommender System** — Svetlin Bostandjiev, John O’Donovan, Tobias Höllerer. 2012. *ACM RecSys*, 35–42. [作者大学全文](https://sites.cs.ucsb.edu/~holl/pubs/Bostandjiev-2012-RecSys.pdf)。已核对设计与32人用户研究。

用户能编辑画像权重、调整不同推荐来源并观察结果变化。作者报告理解与用户体验方面的收益，也承认完整交互条件与其他条件的准确性比较存在不公平因素。这可作为兴趣编辑与解释界面的先例，不能作为长期兴趣扩展证据。[原文，§4、§7.2.3–7.3](https://sites.cs.ucsb.edu/~holl/pubs/Bostandjiev-2012-RecSys.pdf)。

## 对当前项目可以作出的判断

以下是对论文与项目的综合判断，不是这些作者评价过 OtherWise。

| 当前设计 | 文献提供的理由 | 仍需我们验证的部分 |
|---|---|---|
| 保留多个单独兴趣，避免只取一个中心 | PURS 讨论多个兴趣区域，以及单一区域会吞入本应意外的项目 | 最近兴趣距离是否比平均、簇或其他模型更符合用户体验 |
| 在可调范围内推荐陌生主题 | PURS、Adamopoulos 的意外性模型；Auralist 的个体差异 | 固定半径、范围与中点排序是否合适；这些数值没有心理校准 |
| 降低同一列表中的重复 | MMR 的相关性与重复度权衡 | 是否增加有价值的发现，而不仅是提高离线差异指标 |
| 明确保存兴趣后再用于画像 | 用户控制界面的研究；Hidi & Renninger 的兴趣阶段区分 | 保存是否代表持续兴趣；确认是否给用户实际控制 |
| Galaxy 呈现跨领域主题与探索路径 | 可视化与解释研究提供界面先例 | 是否帮助理解与探索；二维布局不是兴趣、知识或观点的测量 |
| 保存新兴趣后逐步扩展范围 | 属于我们可检验的设计假设 | 本次论文没有直接支持“每次保存加 0.01、最多八次”的规则 |

项目依据：[当前说明](../../README.md)、[探索引擎](../../explorer.py)、[参数说明](../parameter-guide.md)、[扩展使用说明](../extension-guide.md)。学术依据：[PURS](https://arxiv.org/pdf/2106.02771)、[Auralist](https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf)、[MMR](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf)、[交互式可视化](https://julita.usask.ca/Texte/ht84nagulendra.pdf)、[兴趣发展模型](https://works.swarthmore.edu/fac-education/12/)。

## 下一步怎样验证“兴趣变广”

这部分是研究建议，不是已完成的实验。先与普通最近邻推荐、随机主题和多样性排序基线比较，区分“我们选择的范围”与“列表去重”的贡献。问用户：是否以前就知道、是否觉得意外、是否对自己有意义、是否想继续了解，并在之后数周观察主动回来探索与持续兴趣的自报。范围控制与 Galaxy 可以单独比较，以免无法判断哪一部分起作用。设计动机来自上面的意外性、偶遇体验及兴趣发展研究，具体实验需要我们另行设计。[PURS](https://arxiv.org/pdf/2106.02771)、[Binst 2025](https://imec-publications.be/server/api/core/bitstreams/d53afde9-0a02-4872-a8bf-5861c0e69281/content)、[Hidi & Renninger](https://works.swarthmore.edu/fac-education/12/)。

## 如果只读六篇

1. **Holtz 2020**：最贴近日常内容消费的风险证据，务必读个体多样性的条件限制。
2. **Chaney 2018**：解释推荐反馈怎样影响后续数据。
3. **Nguyen 2014**：防止把风险写成所有系统的必然后果。
4. **PURS 2020**：最贴近多个兴趣区域与适中意外性的算法先例。
5. **Auralist 2012**：最贴近探索程度与用户控制的建议。
6. **Nagulendra & Vassileva 2014**：最贴近可视化、理解与控制的界面先例。

如果还想强调“触发新兴趣”，接着读 **Binst 2026** 和 **Hidi & Renninger 2006**；如果要讨论政治后果，再读 **Gauthier 2026** 与 **Nyhan 2023**。

## 建议的保守英文项目论述

> Personalized recommendations can make discovery more relevant, but some recommendation settings are associated with narrower consumption or self-reinforcing feedback. Evidence varies across systems, and content diversity is not the same as psychological interest breadth or reduced polarization. OtherWise explores a complementary approach: helping people discover related but unfamiliar topics, with explicit control over how far they explore.

前两句依据为上文 Holtz、Anderson、Chaney 与 Nguyen，政治结果限制依据 Nyhan 与 Gauthier；最后一句为当前项目的设计定位，没有声称已证实用户效果。[Holtz](https://ide.mit.edu/wp-content/uploads/2020/03/SSRN-id3555927.pdf)、[Anderson](https://www.cs.toronto.ca/~ashton/pubs/alg-effects-spotify-www2020.pdf)、[Chaney](https://arxiv.org/pdf/1710.11214)、[Nguyen](https://archives.iw3c2.org/www2014/proceedings/proceedings/p677.pdf)、[Nyhan](https://www.nature.com/articles/s41586-023-06297-w)、[Gauthier](https://www.nature.com/articles/s41586-026-10098-2)。

## 可用于英文 Related Work 的方案段落

> OtherWise builds on research on unexpected recommendations, serendipity, and user control. PURS represents multiple user interests in an embedding space and balances unexpectedness with relevance. Auralist argues that people differ in how much discovery they want and proposes letting users adjust that level. Interactive visualization research also shows how users can understand and control filtering. OtherWise brings these ideas into a topic exploration tool. Its goal is to help users find unfamiliar but meaningful directions; whether those discoveries become lasting interests remains a question for user studies.

前三项依据：[PURS](https://arxiv.org/pdf/2106.02771)、[Auralist](https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf)、[交互式可视化](https://julita.usask.ca/Texte/ht84nagulendra.pdf)。最后两句描述项目目标和待验证问题。[当前项目](../../README.md)。
