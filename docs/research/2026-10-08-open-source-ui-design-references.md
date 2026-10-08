# OtherWise 开源 UI 设计参考

研究日期：2026-10-08。建议优先参考 Telegram UI 的紧凑列表与分组、shadcn/ui 的桌面视觉层级，以及 Radix 的菜单与弹窗行为。保留 OtherWise 的深蓝和浅绿色风格，先通过现有原生前端打磨界面；若需要实际复用组件，再单独评估 Web Awesome Core。以下优先级是针对 OtherWise 的设计判断。

OtherWise 当前使用原生 HTML/CSS/ES modules，包含 Chrome side panel 和独立 dashboard，没有 React/Tailwind 依赖。Discover 已有 topic-list + topic-detail 主从布局、cards/single 切换和 Save/Search/More 操作；Interests 已有可移除标签，Settings 已有折叠分组。本次重点是如何打磨这些结构的层级、密度、控件、状态与响应式，不把已有功能当作新设计。[本地前端](../../extension/ui/app.js)、[样式](../../extension/ui/workbench.css)、[依赖](../../package.json)

## Telegram UI

### Telegram UI 组件库

[TelegramUI GitHub](https://github.com/telegram-mini-apps-dev/TelegramUI) · [组件预览](https://tgui.xelene.me/) · [MIT 许可证](https://github.com/telegram-mini-apps-dev/TelegramUI/blob/main/LICENSE)

**项目事实。** 这是面向 Telegram Mini Apps、受 Telegram 界面启发的 React 组件库，包名为 `@telegram-apps/telegram-ui`。仓库说明署名 mainsmirnov，赞助方为 TON Foundation。源码提供浅色／深色、iOS／base 平台样式，并通过 CSS 变量设置字体与颜色。[README](https://github.com/telegram-mini-apps-dev/TelegramUI)、[依赖](https://github.com/telegram-mini-apps-dev/TelegramUI/blob/main/package.json)、[主题源码](https://github.com/telegram-mini-apps-dev/TelegramUI/blob/main/src/components/Service/AppRoot/AppRoot.module.css)

**适合借鉴的部分（设计判断）。** 在项目的 Storybook 查看了 Cell 和深色 Section 示例。它的价值在于把标题、次级说明、前后图标和操作位置组织清楚，适合 OtherWise 的窄侧栏。具体可参考：

| 组件与预览 | OtherWise 对应位置 | 借鉴重点 |
| --- | --- | --- |
| [Cell](https://tgui.xelene.me/?path=/docs/blocks-cell--documentation) | Discover 主题列表、待确认兴趣 | 标题与领域说明的层级，图标与尾部信息对齐，清楚的整行交互反馈。 |
| [Section](https://tgui.xelene.me/?path=/docs/blocks-section--documentation) | Settings 现有分组 | 用组标题、组内分隔和组外说明整理表单，减少每一行重复套卡片。 |
| [Chip](https://tgui.xelene.me/?path=/docs/form-chip--documentation) | 已保存兴趣标签 | 统一高度、间距和移除按钮，长名称也保持可读。 |
| [Placeholder](https://tgui.xelene.me/?path=/docs/blocks-placeholder--documentation) | 初次使用、无推荐结果 | 图形、简短解释与下一步动作组成完整空状态。 |
| [Skeleton](https://tgui.xelene.me/?path=/docs/feedback-skeleton--documentation) 与 [Snackbar](https://tgui.xelene.me/?path=/docs/feedback-snackbar--documentation) | 加载、保存与撤销反馈 | 让短暂状态有一致的位置和表达，避免每次操作都弹对话框。 |

字体和行高要按 OtherWise 的内容与侧栏宽度调整。当前部分辅助文字使用 10px，可优先试验提高可读性，同时保留紧凑列表；Telegram 的整套字号与移动端导航无需原样套用。[本地样式](../../extension/ui/workbench.css)

**适配判断。** 原生 HTML 页面不能直接运行它的 React 组件。主题源码有 Telegram CSS 变量的默认值，`useAppearance` 也提供普通浏览器的主题订阅，因此该库可以在 Telegram 外部运行；真正接入 OtherWise 仍需增加 React 与构建适配。现阶段更适合参考结构和视觉规则。[AppRoot](https://github.com/telegram-mini-apps-dev/TelegramUI/blob/main/src/components/Service/AppRoot/AppRoot.tsx)、[浏览器主题处理](https://github.com/telegram-mini-apps-dev/TelegramUI/blob/main/src/components/Service/AppRoot/hooks/useAppearance.ts)

### Telegram Web A 完整应用

[Telegram Web A GitHub](https://github.com/Ajaxy/telegram-tt) · [应用](https://web.telegram.org/a/) · [UI 源码目录](https://github.com/Ajaxy/telegram-tt/tree/master/src/components/ui)

这是实际 Telegram Web A 客户端的完整源码，使用自有 Teact 框架，仓库标明 GPL-3.0。它适合研究完整应用的列表、详情、导航与动效如何协作；对于复用几个控件，前面的 Telegram UI 更直接。本次把它作为产品交互参考，未登录应用或验证登录后的具体流程。[项目说明](https://github.com/Ajaxy/telegram-tt)、[许可证](https://github.com/Ajaxy/telegram-tt/blob/master/LICENSE)

## 值得优先看的项目

| 项目 | 官方入口与许可证 | 技术栈与定位 | 对 OtherWise 的主要价值 |
| --- | --- | --- | --- |
| **shadcn/ui** | [GitHub](https://github.com/shadcn-ui/ui) · [组件](https://ui.shadcn.com/docs/components) · [完整 Blocks](https://ui.shadcn.com/blocks) · [MIT](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md) | 可复制修改的组件代码体系；官方 Blocks 面向 React，手动安装要求 Tailwind CSS。 | 统一卡片、按钮、输入框、浮层与浅／深色主题；最适合作为视觉与组件规范参考。 |
| **Primer** | [CSS GitHub](https://github.com/primer/css) · [React GitHub](https://github.com/primer/react) · [官方组件](https://primer.style/product/components) · [CSS MIT](https://github.com/primer/css/blob/main/LICENSE) · [React MIT](https://github.com/primer/react/blob/main/LICENSE) | GitHub 的设计系统，分别有 Sass/CSS 与 React 实现。 | 紧凑列表、附加说明、选择状态、空状态；特别适合窄侧栏的已有内容列表。 |
| **Mantine** | [GitHub](https://github.com/mantinedev/mantine) · [文档与演示](https://mantine.dev/) · [页面／组件组合示例](https://ui.mantine.dev/) · [MIT](https://github.com/mantinedev/mantine/blob/master/LICENSE) | React 组件、hooks 与主题体系。 | 兴趣搜索、多选、标签输入、滑块和设置表单；适合作为交互细节素材库。 |
| **Radix Primitives** | [GitHub](https://github.com/radix-ui/primitives) · [文档](https://www.radix-ui.com/primitives/docs/overview/introduction) · [MIT](https://github.com/radix-ui/primitives/blob/main/LICENSE) | 无默认样式的 React 行为组件，关注焦点、键盘和可组合结构。 | 检查现有弹层、菜单和范围控件的行为是否完整；视觉灵感相对少。 |
| **Web Awesome Core** | [GitHub](https://github.com/shoelace-style/webawesome) · [文档与演示](https://webawesome.com/docs) · [Core MIT](https://webawesome.com/license) | 基于 Web Components／Lit 的自定义元素；可按需本地导入。 | 本组最接近现有原生前端的接入方式，可小范围试用 slider、tag、dialog 等 Core 控件。 |
| **Sigma.js** | [GitHub](https://github.com/jacomyal/sigma.js) · [文档](https://www.sigmajs.org/docs/) · [Storybook](https://www.sigmajs.org/storybook/) · [综合 demo](https://www.sigmajs.org/demo/) · [MIT](https://github.com/jacomyal/sigma.js/blob/main/LICENSE.txt) | JavaScript／TypeScript + WebGL + Graphology 的图网络渲染库，**不是 UI 组件库**。 | Map/Galaxy 的邻居高亮、点击节点、标签与缩放交互参考；不应为换外观直接替换渲染器。 |

### shadcn/ui 的整体视觉规范

**项目事实。** 官方将其定位为开放组件代码及分发体系，开发者可以直接修改拿到的代码；Blocks 提供 React 页面组合，手动安装明确要求 Tailwind CSS。当前组件文档也有 Base UI、React Aria、Radix UI 等入口，不能把整套项目简单描述成“全部只是 Radix 的样式”。[介绍](https://ui.shadcn.com/docs)、[安装](https://ui.shadcn.com/docs/installation/manual)、[Combobox](https://ui.shadcn.com/docs/components/combobox)

**适合借鉴的部分（设计判断）。** 看 [Card](https://ui.shadcn.com/docs/components/base/card)、[主题 tokens](https://ui.shadcn.com/docs/theming) 和 [dashboard 示例](https://ui.shadcn.com/view/new-york-v4/dashboard-01)：把表面、正文、弱化文字、边框、焦点、主按钮各自设成少量一致的规则。对 OtherWise，最有用的是统一现有 topic-detail 的标题／说明／操作区，使 Search 主动作、Save 次动作、More 收纳的层级更一致，以及让 side panel 和 dashboard 使用同一套控件尺寸关系。保留 OtherWise 自己的色彩和探索感。

**适配判断。** 优先抽取视觉规则并重写为现有 CSS；React/TSX 和 Tailwind class 不能直接粘贴到当前页面中运行。官方 [Command 示例](https://ui.shadcn.com/docs/components/radix/command) 可启发主题搜索的分组结果、空结果和快捷键提示，但没有必要仅为此迁移整个前端。

作为已有 Discover 主从布局的具体对照，还可看 [Mail 示例](https://v3.shadcn.com/examples/mail)。这是官方保留的 v3 示例：导航、列表、详情用轻边框和选中背景分区，内容与工具动作有清楚层级。可借鉴排版关系，邮件功能与多栏数量不适合直接照搬到窄侧栏。

### Primer 的紧凑列表

**项目事实。** [ActionList](https://primer.style/product/components/action-list/) 展示单列交互项，可组合主文字、说明、前后图标和侧边信息，并有单选、多选、分组、危险动作等示例。[Blankslate](https://primer.style/product/components/blankslate/) 提供空状态组件。[Primer CSS](https://github.com/primer/css) 的源码使用 Sass/SCSS；官方 React 组件是另一套实现，不能把 React 示例当成 CSS 库直接提供的完整交互。

**适合借鉴的部分（设计判断）。** 对现有 topic-list，统一主题名、领域说明、右侧指示及选中背景的位置；使用一致的行高和缩进，让用户更快扫读。Interests 的待确认项、历史反馈列表也可复用同样的信息层级。空状态要区分“还没有兴趣”“筛选无结果”“数据尚未加载”，每种给出对应的下一步，而不是只放一句“暂无数据”。

**适配判断。** 以设计规范和少量 CSS 为主，比直接引入 React 实现轻。若使用 CSS 包，应先编译并限定作用范围，避免全局样式覆盖现有控件；涉及菜单和复合选择器时，行为仍需实现。紧凑不等于把所有点击目标缩小。

### Mantine 的搜索与参数控制

**项目事实。** Mantine 是 React 组件库。[Combobox](https://mantine.dev/core/combobox/) 文档链接到大量可组合示例，涵盖 select、多选及 autocomplete；[Slider](https://mantine.dev/core/slider/) 演示刻度、格式化数值和 `onChangeEnd`，后者在停止拖动或键盘改变数值时触发。[MantineProvider](https://mantine.dev/theming/mantine-provider/) 负责主题，包含动态样式和样式 nonce 配置。

**适合借鉴的部分（设计判断）。** Interest 搜索可以学习“输入 → 结果分组 → 已选项”的反馈连续性；已有 chip 可进一步统一移除按钮、选中状态和长名称处理。Galaxy 参数区可学习滑块的数值／刻度／单位展示，将“正在调节的预览值”和“需要计算或保存的提交值”说明清楚，减少重计算造成的卡顿和误解。是否在拖动后提交，需要结合现有参数行为决定。

**适配判断。** 主要借交互，不建议为几项控件引入 React 和完整 Provider。其动态样式不是当前 `script-src 'self'` 自动禁止的对象；真正接入仍需按扩展的实际 CSP、打包方式与主题设置验证，不能仅凭 nonce 选项认定已经兼容或不兼容。

### Radix Primitives 的键盘与焦点行为

**项目事实。** 官方说明组件不带默认样式，并处理许多 ARIA、键盘和焦点细节。[介绍](https://www.radix-ui.com/primitives/docs/overview/introduction)、[可访问性](https://www.radix-ui.com/primitives/docs/overview/accessibility)。[Dialog](https://www.radix-ui.com/primitives/docs/components/dialog) 规定 Esc 关闭并把焦点交还触发元素；[Slider](https://www.radix-ui.com/primitives/docs/components/slider) 列明方向键、Home/End 等键盘操作，并区分值变化与提交回调。

**适合借鉴的部分（设计判断）。** 用它检查 OtherWise 现有 More 菜单、参数浮层和确认对话框：打开后焦点在哪、关闭后回到哪、Esc 是否有效、禁用状态是否清楚。对单个连续数值，优先保留原生 range 的浏览器行为，再统一视觉；复杂多拇指控件才值得专门评估。

**适配判断。** 这里的 Primitives 是 React 实现，不是原生 JavaScript 包，也不是完整视觉主题。只照着文档实现一部分行为，不代表自动获得 Radix 的可访问性保障；迁移后的真实页面仍要验证。

### Web Awesome Core 的原生组件接入方式

**项目事实。** 官方提供 [Shoelace 迁移说明](https://webawesome.com/docs/resources/migrating-from-shoelace)，以及按需导入、本地托管、`dist` 与浏览器可直接使用的 `dist-cdn` 说明。[安装与资源路径](https://webawesome.com/docs)。源码包声明了 Lit 依赖与自定义元素导出。[package.json](https://github.com/shoelace-style/webawesome/blob/next/packages/webawesome/package.json)。Core 是 MIT；官网也明确把 Combobox、Patterns、部分数据可视化等标为 Pro，所以不能把官网所有展示都算作免费开源资源。[Core 许可](https://webawesome.com/license)、[组件目录](https://webawesome.com/docs)

**适合借鉴的部分（设计判断）。** [Slider](https://webawesome.com/docs/components/slider/) 的标签、辅助说明、格式化 tooltip 和区间选择适合参数区；[Tag](https://webawesome.com/docs/components/tag/) 的移除事件与可访问名称适合完善已有兴趣标签；[Drawer](https://webawesome.com/docs/components/drawer/) 可作为小屏 Map 详情面板的参考。桌面仍适合保留已有图与详情并列的布局。

**适配判断。** 不需要把应用改成 React，适合挑一个 Core 控件做小规模试验。扩展要将组件、样式和依赖资源打包到本地，把文档中的内联脚本移到现有模块；图标也应使用本地资源 resolver，而不是默认照搬 CDN 示例。[安装](https://webawesome.com/docs)、[图标库配置](https://webawesome.com/docs/components/icon/)。Shadow DOM 的样式需要通过 tokens／公开 CSS parts 调整；本次未做 Chrome 扩展实装验证，也未测量引入后的包大小。

### Sigma.js 的星图交互参考

**项目事实。** Sigma 的核心示例直接在 JavaScript 容器中创建渲染实例，搭配 Graphology，核心不要求 React；官方综合 demo 本身使用 React。[介绍及集成](https://www.sigmajs.org/docs/)。官方列出 hover、clickNode、clickStage 等 [事件](https://www.sigmajs.org/docs/advanced/events/)，并给出 reducers 高亮邻域、标签和 hover 绘制的 [定制方法](https://www.sigmajs.org/docs/advanced/customization/)。

**适合借鉴的部分（设计判断）。** 对已有 Galaxy/Focus，重点看“选中节点 → 明确高亮相关邻居 → 在独立 HTML 面板读详情”的连接、按缩放层级控制标签密度，以及搜索定位后如何持续保留选中状态。这些模式可以在现有渲染器中学习，不要求换库。

**适配判断。** 只有当现有渲染性能、命中检测或定制能力形成明确限制时，再评估渲染库迁移。核心接入仍要解决依赖打包、WebGL 和扩展 CSP；图形库不会自动提供完整的键盘导航和屏幕阅读器详情。它也不决定 OtherWise 的推荐距离或布局语义，画面坐标不能直接当作用户真实兴趣距离。

## 原生扩展接入边界

当前 manifest 的 `extension_pages` 是 `script-src 'self'; object-src 'none'; base-uri 'none'`。因此文档中的远程 JS loader 和内联脚本不能原样用于 OtherWise；实际执行代码要随扩展本地打包。当前没有单独设置 `style-src`，不能笼统声称所有内联样式或 Shadow DOM 样式都被 CSP 禁止。[本地 manifest](../../extension/manifest.json)、[Chrome 官方 CSP 说明](https://developer.chrome.com/docs/extensions/reference/manifest/content-security-policy)

上文只核实了项目文档、源码与许可证，并阅读其演示示例；没有在 OtherWise 中安装依赖或证明某个库已兼容当前扩展。视觉规则与原生 CSS 可以先落地讨论，直接引入库则需要单独的打包与运行验证。中英文文案长度、侧栏宽度、深色模式和现有保存／失败状态，均应在真实 OtherWise 页面中判断。

## 对 OtherWise 的最终建议

1. **侧栏先看 Telegram UI。** 保留已有兴趣标签和主题列表，统一标题／副文、行高、图标、尾部动作与选中反馈。Settings 保留现有折叠分组，学习 Section 的组内与组外信息层级。
2. **桌面页先看 shadcn/ui。** 保留已有列表加详情的结构，打磨导航、列表、内容面板之间的留白和分隔。沿用现有 Search 主动作、Save 次动作、More 收纳的关系，统一按钮和浮层的视觉。
3. **行为细节看 Radix，复杂控件看 Mantine。** 菜单、弹窗、加载、保存、失败与撤销要有一致反馈；搜索、多选、滑块只在确实帮助当前任务时采用。
4. **实际接库优先小范围评估 Web Awesome Core。** 它更贴近当前原生前端，但仍需验证本地打包、样式覆盖和运行表现。Telegram UI、shadcn/ui、Mantine 和 Radix 本次主要作为设计及行为参考。
5. **Galaxy 单独看 Sigma 的交互示例。** 关注搜索定位、选中节点、邻居高亮、标签密度与详情面板的协作，延续现有 Galaxy／Focus 与语义距离规则。

推荐的第一轮范围是字号与间距、列表选中态、按钮层级和设置分组，继续使用 OtherWise 现有的深蓝、浅绿色与星图元素。这些都是供后续设计选择的建议，本次仅新增研究笔记。
