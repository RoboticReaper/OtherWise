# OtherWise 话题池扩展：来源、规模与选择

核查日期：2026-10-05。这份研究记录描述实施前的目录和四种扩展路径；后续实施结果见文末和 data/README.md。

## 结论

**有更大的候选池。最适合下一阶段的是 Wikipedia Vital articles Level 5，再用 Wikidata 补全名称、描述与实体 ID。** 它比目前使用的 Wikimedia Expanded 清单更细，仍有人工维护的知识领域结构，比较符合日常兴趣探索。先取消或提高当前每领域 160 条的导入上限，也能释放现有来源的部分空间。

推荐把 **1–3 万条通过筛选的话题**作为工程试验目标，而不是声称已经存在这么多可直接使用的话题。这是建议，必须通过实际导入、去重、描述质量检查和领域抽样确认。外部清单条数、知识图谱实体数、论文数和 OtherWise 可用话题数是不同的指标。

## 实施前的实际来源

- 当前 [原始平衡目录](../../data/archives/topics_balanced.json) 共 **3,452** 条：**718 ProductSpace 自编条目 + 2,734 Wikidata 条目**；[原始平衡目录元数据](../../data/archives/catalog_metadata_balanced.json) 记录 23 个领域与每领域最多 160 条，18 个领域已经到上限。
- 外部候选来自 [Wikimedia Expanded 清单](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded)，不是从整个 Wikidata 随机抽取。[导入脚本](../../scripts/import_balanced_catalog.py) 排除 Biography 与部分具体作品、建筑、公司、学校等分节，再获取 Wikidata 描述、过滤、去重，按分节轮转选择。
- `source_item_count=7777` 是本地上次导入在分节排除后得到的唯一 QID 数，**不是取消上限后的可用数量**；后面仍有描述、实体类型、重复和领域上限筛选。本地源页面与实体缓存缺失，本次没有重跑完整导入，无法给出解除上限后的准确结果。
- 后端默认加载这份本地目录；推荐运行时不查询 Wikimedia/Wikidata/OpenAlex。此前 OpenAlex 版本已经归档：[openalex_metadata.json](../../data/archives/openalex_metadata.json) 记录 5,228 条（718 自编 + 4,510 OpenAlex），从 4,516 个 OpenAlex Topics 去掉 6 个同名项后得到。数量更大不代表更适合日常兴趣。

## 四种扩展路径

| 路径 | 已核查的外部规模 | 对 OtherWise 的适配与边界 |
|---|---|---|
| 放宽当前 Wikimedia Expanded 选择 | 清单设计目标 **10,000**；本地旧快照分节排除后为 **7,777 QID** | 改动最小，复用现有领域映射与 Wikidata 补全。筛选后新增量未知，且扩容空间有限。官方清单按领域配额组织，并说明有些部分仍需清理。[清单说明](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded) |
| **Vital articles Level 5** | **49,854** 条，页面计数更新于 **2026-10-03**；目标 50,000。People 占 14,181，整节排除后算术余量 **35,673** | 首选。包括 Everyday life、Arts、Technology 等分表；比当前来源更细。35,673 仍包含具体地方、作品、生物种类等，尚未通过 OtherWise 的筛选，也与现有目录重叠。该清单针对英语 Wikipedia，不能当作文化中立的兴趣全集。[官方清单与计数](https://en.wikipedia.org/wiki/Wikipedia:Vital_articles/Level/5) |
| 从 Wikidata / 英语 Wikipedia 按类型扩展 | Wikidata 统计页显示 **123,538,170 items**；英语 Wikipedia 页面显示约 **725 万 articles**，均为访问时动态值 | 长期空间很大，但前者是实体、后者是文章，不能换算成同样数量的兴趣。应按已有领域与类型白名单取候选、要求英文名称/描述及 Wikipedia 链接，排除人、消歧义、列表等，再评审具体作品/地点是否属于产品范围。所有条件组合后的数量本次未测。[Wikidata 统计](https://www.wikidata.org/wiki/Wikidata:Statistics)、[英语 Wikipedia 计数](https://en.wikipedia.org/wiki/English_Wikipedia) |
| OpenAlex Topics / Works | 官方当前分类体系 **4,516 Topics**；Works 页面显示约 **3.32 亿 scholarly documents** | Topics 没有数量级扩容空间；Works 是论文、书章、数据集等记录，不是话题目录。它适合“学术研究方向”模式或给话题关联阅读材料；将论文标题抽成兴趣话题需要额外构建与验证，不建议作为本次通用池扩容主源。[Topics](https://help.openalex.org/data/topics/)、[Works](https://help.openalex.org/data/works/) |

## 可实施的获取方式与许可

1. **清单 → 实体：**用 MediaWiki `action=parse` 获取清单分表的 wikitext、链接和 revision ID；Vital 分表通常指向英语文章，再通过 `action=query&prop=pageprops` 的 `wikibase_item` 取得 QID。不要把页面上所有导航链接都当作条目；保存所属分节与源修订号。[Parse 文档](https://www.mediawiki.org/wiki/API:Parsing_wikitext)、[Pageprops 示例](https://www.mediawiki.org/wiki/API:Pageprops)
2. **实体 → 描述：**复用 Wikidata 名称/描述/类型查询。官方文档建议小批实体使用 API；类型条件查询用有明确范围的 SPARQL；很大的结果集用 dump，避免尝试用公共查询服务遍历全库。清单扩容阶段仍可采用离线生成固定目录，再由运行时读取。[Wikidata 数据访问](https://www.wikidata.org/wiki/Wikidata:Data_access)
3. **许可分开记录：**Wikidata 结构化数据为 **CC0**；Wikipedia/Meta 清单文字、组织与复制的文章文字涉及 **CC BY-SA 4.0**，需要保留适当来源与许可信息。采用 Wikidata 描述不能自动把复制的 Wikipedia 清单结构变成 CC0。OpenAlex 数据为 **CC0**；关联论文原文另有自己的许可。[Wikidata 许可](https://www.wikidata.org/wiki/Wikidata:Licensing)、[Wikipedia 再使用说明](https://en.wikipedia.org/wiki/Wikipedia:Copyrights)、[Meta 清单页许可](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded)、[OpenAlex 数据许可](https://help.openalex.org/data/how-its-built/)

## 下一阶段建议与验证口径

保持 718 条自编日常兴趣作为基础，先收集 Expanded 与 Vital Level 5 的候选并按 QID 合并，再去除同名/同义重复、无描述与超出产品范围的条目。**目录容量与推荐平衡应分别处理：**保留较大的候选目录，在推荐排序或采样时控制领域覆盖；是否取消固定领域上限是后续设计选择，研究阶段尚未实现。

每次导入报告分别记录：源清单条目数 → 可解析的唯一 QID → 通过内容/描述筛选的数量 → 去重后新增数量 → 最终可用数量，并给出各领域分布与抽样质量。以此确认扩容是否增加用户能理解、值得探索的新话题，而不只是增加实体数量。

## 后续实施快照

本轮已采用 Vital Articles Level 5，保留原有 3,452 条记录，新增 28,185 条，总计 **31,637 个主题、23 个领域**，取消领域截断。源清单解析出 34,271 条候选，解析到 34,266 个唯一 QID；筛选与去重后的新增量才是最终扩容量。目录、逐条来源和筛选统计见 [data/README.md](../../data/README.md) 与 [catalog_metadata.json](../../data/catalog_metadata.json)。
