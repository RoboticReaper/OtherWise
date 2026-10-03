# Semantic Focus and Galaxy Exploration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将真实语义 Focus、单击/双击地图入口和可开关的探索点亮模式整合进现有 OtherWise 扩展与 Dashboard。

**Architecture:** 全局 Galaxy 继续使用原有固定缓存。局部 Focus 以原始 catalog 向量距离为半径、全局投影为方向，通过独立接口与请求通道获取推荐。保留 Map 组件实例，分别管理持久兴趣、窗口内临时焦点、动画和有限缓存。

**Tech Stack:** Python/FastAPI/NumPy，原有 explorer 推荐器，Chrome MV3，原生 ES modules、Canvas/SVG/CSS；Node 24.19.0、现有 Python 3.13.1 venv。无需引入 React 或 Vite。

**Spec:** `docs/superpowers/specs/2026-10-03-focus-exploration-design.md`（用户于 2026-10-03 确认）。实现前完整阅读该文档。

## Global Constraints

- 使用已有产品 worktree `/Users/arthurfu/.codex/worktrees/otherwise-galaxy-product/OtherWise`，分支 `codex/otherwise-development`；计划起点为 `7ab7990`。执行前检查状态，不切换原 checkout。
- “全局坐标完全沿用缓存；Focus 是独立的局部投影。”不重算 UMAP，不用屏幕距离排名。
- “只展开一层直接近邻”；已保存中心及其 10 个真实近邻、单独探索过的点共同组成点亮集合。
- “进入 Focus 本身不产生网络请求。”显式 Get ideas 只发送当前 catalog ID、数据版本及七项推荐参数。
- `acos(clamp(cosine, -1, 1)) / pi`，768 维；canonical topic ID 关联数据。原始名称与描述保持原样，中文仅为 UI。
- “Focus 结果使用独立、有上限的内存缓存（最多 20 个请求键）。”默认探索开关关闭；不增添长期个人记录。
- 单击初始判定 250ms；普通命中目标至少 24px，触屏优先 44px；运行中响应减少动态效果。
- “不部署、不推送远端、不修改队友仓库。”保留安装路径与用户数据，不扩大扩展权限。

## Review Focus

- 原始 `.npy` 在 cache-load 路径提前归一化：版本必须与 Galaxy 原始数组身份相同，而不是误报冲突（Task 1）。
- Dashboard 与侧栏同时请求、切换中心或撤销权限：只能取消自己的旧请求，不能让过期响应复活（Task 3）。
- 两个兴趣覆盖同一点，或者用户搜索过被移除兴趣的邻居：移除后仍保留正确的点亮来源（Task 2、4）。
- 同坐标、跨领域灰色点、拖动后点击和双击：仍可到达每个 topic，不能误保存或误跳转（Task 4、5）。
- 保存或语言更新触发父组件重绘：不能重播开场、重发请求、丢相机或留下脱离 DOM 的动画循环（Task 6）。

## Files and ownership

| Task | 文件与责任 |
| --- | --- |
| 1 | `service/engine.py`, `service/api.py`：真实向量 Focus API；`tests/test_focus_service.py`, `tests/test_focus_api.py` |
| 2 | 新增 `extension/core/focus-contract.js`, `extension/ui/focus-logic.js`, `extension/ui/exploration-logic.js`；纯协议、投影、集合运算；对应三个 `extension/tests/*.test.js` |
| 3 | 新增 `extension/focus-transport.js`；修改 `controller.js`, `background.js`, `bridge.js`, `core/index.js`；受保护通信、设置与轨迹；现有及新增 controller/transport tests |
| 4 | 修改 `extension/ui/galaxy.js`, `galaxy.css`, `galaxy-i18n.js`；新增 `star-activation.js` 及其测试、`scripts/test_galaxy_interactions_browser.mjs`；全局点亮与手势 |
| 5 | 新增 `extension/ui/focus.js`, `focus.css`, `focus-orb.js`, `focus-stars.js`, `focus-i18n.js`；视觉组件与原语；新增 `scripts/test_focus_view_browser.mjs`, `docs/focus-animation-provenance.md` |
| 6 | 新增 `extension/ui/focus-session.js`, `map-workspace.js`；修改 `app.js`, `i18n.js`, `dashboard.css`, 两个 HTML 入口、`dev-preview.js`；集成及浏览器回归 |
| 7 | 构建版本、安装指南、验证记录和安装目录交付 |

共享文件由对应任务所有者修改；其他任务通过下方接口连接，不同时编辑 `app.js` 或 controller。
Task 1 与 2 可并行；Task 3 接 1/2；Task 4、5 接 2 并可独立开发；Task 6 汇合 3/4/5；Task 7 最后执行。

## Shared contracts

`FocusIdentity = {catalog_sha256, model, embedding:{sha256,dtype,shape:[number,768]}}`。
请求 `POST /api/focus` 为 `{topic_id, ...FocusIdentity, ...RecommendationOptions}`。
七项 options 沿用 `recommendation-options.js`：limit=10、radius=.28、expansion=.07、overlap=.015、diversity=.20、max_overlap_fraction=.20、randomness=.03。

响应 `FocusEnvelope = {schema_version:1, algorithm_version:'catalog-focus-band-v1', seed_id, ...FocusIdentity, recommendations}`。
每条 recommendation 沿用现有 `{id,topic,domain,description,nearest_interest,distance,boundary_offset,zone}`；生产文本以本地 catalog 为准。
错误：未知 ID/坏参数 422、数据版本冲突 409、认证 401、频率 429、未就绪/计算错误 503，消息不回显输入。

`MapSearchContext` 为 `{source:'galaxy'}` 或 `{source:'focus',centerId}`；省略 context 时仍走原 Discover 行为。
Focus 身份校验使用 layout.metadata 的原 catalog/model/embedding 数据；布局算法版本不是推荐算法版本。

## Task 1: 真实 catalog Focus 接口

**Interfaces:**
- Produces: `RecommendationEngine.focus_identity() -> dict`；`recommend_focus(topic_id: str, *, expected_identity: dict, **seven_options) -> FocusEnvelope`。
- API 使用严格 `FocusRequest` 和嵌套 embedding model；输入字段与 Shared contracts 完全一致。

- [ ] **1. 写失败测试。** 在两个新 Python 文件中复用现有 API TestClient 模式，另建包含中心的 768D 向量 fixture；不要改变原 2D service fixtures。固定向量以 `[cos(pi*d),sin(pi*d),0,...]` 表示到中心的已知距离。

```python
# test_focus_uses_catalog_vector_without_encoding
result = engine.recommend_focus('Center', expected_identity=engine.focus_identity(), randomness=0)
assert result['seed_id'] == 'Center'
assert all(abs(r['distance'] - known_distances[r['id']]) < 1e-6 for r in result['recommendations'])
assert encode_calls == 0
# test_focus_raw_identity_survives_cache_reload
assert reloaded.focus_identity()['embedding']['sha256'] == hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest()
```

另测与原 ranker 输出一致、稀疏结果不扩大距离带、重排 ID 对应、严格参数/多余 history/keywords 字段、原始 float32/非连续数组身份、缓存命中与首次生成、409/422、两个 API 共用认证/限流/信号量、失败后释放信号量。`test_focus_identity_matches_galaxy_metadata` 使用原 `fast_projection` helper 避免跑 UMAP。
- [ ] **2. 跑红。** `.venv/bin/python -m pytest -q tests/test_focus_service.py tests/test_focus_api.py`；预期仅新增功能缺失相关失败。
- [ ] **3. 实现接口。** 在 cache-load 路径归一化前、注入向量归一化前保留 raw identity；新编码数组取实际写入 npy 的字节。构建 title→index 查找，复用 `explorer.recommend`，种子直接取 `topic_vectors[[index]]`，不得调用旧 `engine.recommend()`。扩展 RequestBoundary 保护新路径，复用并发/错误边界；原接口不变。
- [ ] **4. 跑绿。** 上述命令及 `.venv/bin/python -m pytest -q tests/test_service.py tests/test_api.py tests/test_explorer.py tests/test_galaxy.py` 全部通过。
- [ ] **5. 提交。** 仅提交此任务文件：`feat: add catalog-backed Focus recommendations`。

## Task 2: 可验证的协议、投影和探索集合

**Interfaces:**
- `focusIdentity(metadata) -> FocusIdentity`；`buildFocusRequest(seedId,identity,options,catalogById) -> request`；`validateFocusResponse(raw,request,catalogById) -> FocusEnvelope`，位于 `core/focus-contract.js`。
- `projectFocus(data,seedId,recommendations=[],suppressed=[]) -> {seedId,nodes}`，位于 `ui/focus-logic.js`。node 包含 canonical record、distance、x/y、isNeighbor、isRecommendation。半径比例 `K=1000`，只用已知真实距离；中心为 `(0,0)`。
- `explorationSets(data,state) -> {saved,nearby,explored,lit}`，返回 Set，位于 `ui/exploration-logic.js`。

- [ ] **1. 写失败测试。** 创建 `focus-contract.test.js`, `focus-logic.test.js`, `exploration-logic.test.js`，使用自足的小 catalog/layout fixture。

```js
assert.ok(Math.abs(Math.hypot(point.x,point.y) - 1000 * point.distance) < 1e-9);
assert.deepEqual(projectFocus(data,'A',[B]).nodes.find(n=>n.id==='B'),
  projectFocus(data,'A',[C,B]).nodes.find(n=>n.id==='B'));
assert.deepEqual([...explorationSets(data,state).lit].sort(), ['A','B','E']);
assert.throws(()=>validateFocusResponse({...valid,seed_id:'wrong'},request,data.byId));
```

补测缓存近邻与候选去重、同坐标角度确定性、输入顺序/语言/窗口无关、不改变来源数组；点亮只展开一层、多个中心重叠、移除后仍保留 E、未知 custom ID 不造坐标、suppressed 只过滤候选而不隐藏上下文。协议测试覆盖所有身份字段、重复/未知/中心 ID、超 limit、NaN/缺失距离、nearest_interest、距离带 `1e-6` 容差；请求不包含 profile 字段。
- [ ] **2. 跑红。** `node --test extension/tests/focus-contract.test.js extension/tests/focus-logic.test.js extension/tests/exploration-logic.test.js`，确认新增导出/行为缺失。
- [ ] **3. 实现纯函数。** projection 用 `atan2` 全局坐标差，重合时使用稳定 ID hash 角度；不按批次重标定。验证成功后用本地 catalog 替换服务文本。点亮定义直接照 spec，不读取二维距离或当前推荐作为区域来源。
- [ ] **4. 跑绿。** 上述命令及 `node --test extension/tests/galaxy-logic.test.js` 全部通过。
- [ ] **5. 提交。** `feat: define stable Focus geometry and exploration rules`。

## Task 3: 独立请求、设置与搜索来源

**Interfaces:**
- 新增 `createFocusTransport({catalog,loadIdentity,getConnection,hasEndpointPermission,fetchImpl})`，返回 `request(owner,{requestId,topicId,options})`, `cancel(owner,requestId?)`, `invalidate()`, `subscribeInvalidation(listener)`。owner 由可信后台 port 对象确定，不接受 UI 伪造 owner；getConnection 返回规范化 endpoint/accessToken 与请求失效 epoch。
- Controller 新增 `focusRecommendations(owner,{requestId,topicId})`, `cancelFocus(owner,requestId?)`, `subscribeFocusInvalidation(listener)`；`loadIdentity` 是新可选构造依赖，仅 Focus 使用。options 始终读当前设置。
- Bridge 新增 `requestFocus(topicId,{requestId}) -> Promise<FocusEnvelope>`, `cancelFocus(requestId?)`, `subscribeFocusInvalidation(fn)`；`search(topic,provider,context?)` 保持旧调用兼容。

- [ ] **1. 写失败测试。** 新增 `focus-transport.test.js`，扩展 controller/background/core tests，使用 deferred 响应与现有 fake Chrome harness。

```js
assert.deepEqual(after.approved,before.approved);
assert.deepEqual(after.recommendations,before.recommendations);
assert.equal(after.focus,before.focus);
assert.equal(requestBody.keywords,undefined);
assert.equal(ownerBSignal.aborted,false); // 取消 A 不能取消 B 或 Discover
assert.equal(state.settings.galaxyExplorationMode,false); // 旧状态迁移默认值
```

必须覆盖：零兴趣 Focus、没有显式 request 时零上传、权限检查过程中 reset、接收前撤销权限、两个窗口相同 requestId、返回/关闭后响应、endpoint/token/参数变化、错误不写 lastError 到 Discover、表现设置不改变 generation/推荐请求、未保存起点可形成搜索轨迹但不进入 approved/explored；公共 ACTION 不能伪造该内部事件。
- [ ] **2. 跑红。** `node --test extension/tests/focus-transport.test.js extension/tests/controller.test.js extension/tests/background.test.js extension/tests/core.test.js`。
- [ ] **3. 实现独立通道。** 背景新增名为 `otherwise-focus` 的 runtime Port，复用 own-page 验证；用 port 对象作为 owner，断开只取消该 owner。消息为 `{type:'request',requestId,topicId}` / `{type:'cancel',requestId}`，响应为 `{requestId,result}` / `{requestId,error}`，失效广播为 `{type:'invalidated'}`。严格验证消息，不扩大普通 ACTION 权限。继续使用普通消息通道处理持久状态。
- [ ] **4. 实现状态边界。** Focus 请求超时 30s，响应上限 150000 字符，发起/接收均检查连接权限与失效代次。RESET、清除来源/派生数据、端点/密钥/参数变化及权限撤销使 Focus 请求和缓存失效；保存/移除兴趣、语言或纯显示开关不取消独立 Focus 请求。加 boolean 设置白名单、默认/迁移及 presentation-only 排除。SEARCH context 在 controller 用可信 catalog 验证；使用独立内部事件 `EXPLORE_FROM_CATALOG`，不公开该 action。Galaxy 来源 parent 为 null；Focus parent 为真实临时中心；无 context 保留 Discover 行为。
- [ ] **5. 跑绿并提交。** 上述命令和 `npm test` 全部通过；`feat: isolate Focus requests from saved interest state`。

## Task 4: Galaxy 点亮与可靠激活

**Interfaces:**
- `createGalaxyMap` 增加 `onEnterFocus(id)`，并支持 `setActive(active)`；保留 `update/getViewState/destroy`。Map 详情的 Explore 按钮对全部 catalog 星体可用。
- 新增 `createStarActivation({onSelect,onEnterFocus,delay=250,schedule,cancelTimer})`，提供 `click(id)`, `doubleClick(id)`, `cancel()`, `destroy()`，便于用假时钟验证；显式按钮直接调用动作。

- [ ] **1. 写失败测试。** 新增 `star-activation.test.js` 和 `scripts/test_galaxy_interactions_browser.mjs`。后者在独立浏览器测试页挂载真实 createGalaxyMap，以 callback spy 验证进入动作，不依赖尚未接入的 Focus 页面；沿用原脚本的临时浏览器/本地静态服务方式。

```js
activation.click('A'); clock.tick(249); assert.deepEqual(selected,[]);
activation.doubleClick('A'); clock.tick(300);
assert.deepEqual(entered,['A']); assert.deepEqual(selected,[]);
activation.click('B'); activation.cancel(); clock.tick(300); assert.deepEqual(selected,[]);
```

浏览器断言：选灰色星体只开详情、不批量点亮近邻；领域过滤后的点仍可点击；两个兴趣重叠的区域移除一个后正确保留；实际 doubleclick 一次进入；拖动/捏合/pointercancel 不选择。所有世界坐标在开关、保存、移除后不变。
- [ ] **2. 跑红。** `node --test extension/tests/star-activation.test.js`；构建后跑 `node scripts/test_galaxy_interactions_browser.mjs`，新增断言应证明旧行为失败。
- [ ] **3. 实现渲染和激活。** 复用原 pointer/camera 逻辑；所有 catalog 点进入命中表，灰色只影响样式。选择/推荐轮廓不能覆盖探索模式的灰色规则。仅在保存集合增加时对 newlyLit 差集播放光波；显示开关、首次挂载和语言更新不能触发批量“解锁”。最小命中半径 12px/触屏 22px；近距离重叠显示确定性候选列表，提供键盘入口。新增中英文状态说明，暂停时清理激活计时器和动画。
- [ ] **4. 跑绿并提交。** 上述命令、现有 Galaxy logic/i18n tests 通过；`feat: add interactive Galaxy exploration lighting`。

## Task 5: 语义 Focus 场景与动画迁移

**Interfaces:**
- `createFocusView({container,data,snapshot,state,language,presentation,viewState,onEnterFocus,onSave,onDismiss,onSearch,onGetIdeas,onBack}) -> {update({snapshot,state,language}),getViewState(),setActive(active),destroy()}`。
- `snapshot` 为 `{seedId,nodes,status:'local'|'loading'|'ready'|'error',error,requestKey}`；scene 不 fetch、不持久化、不写个人状态。
- `OrbCore(parent,defs,{idPrefix,color})` 提供原语的 `setState/setLook/setSqueeze/update/destroy`；starfield 使用显式 time/motion/view 参数，不导入队友 engine。

- [ ] **1. 写验证场景并跑红。** 新增 `scripts/test_focus_view_browser.mjs`：独立测试页挂载真实 Focus 场景，注入 Task 2 生成的 nodes 与 callback spy，无需 app.js 或在线 API。`node scripts/test_focus_view_browser.mjs` 必须先暴露缺少 Focus 组件。新增 `extension/tests/focus-i18n.test.js` 验证文案键完整及原始主题文本不翻译。
- [ ] **2. 选择性移植。** 从已检查的 `BowenX307/otherwise@8281161` 提取 `orbCore.ts`、`starfield.ts` 的渲染原语，转为无构建依赖的 ES modules，统一领域配色和 SVG ID 前缀。写来源说明；不复制 React 页面、mock API、orbit slots 或物理引擎。
- [ ] **3. 实现场景。** 用 Task 2 nodes 固定定位；镜头只在初次进入、换中心或显式 Reset 时调整，新增批次不自动重排/缩放。提供中心选择、准确距离详情、Get ideas 披露、原有 Save/Search/Dismiss 操作、分页候选文本列表（复用每页 10 条的 paginate）和返回按钮；近邻与候选有明确标记。Focus 内双击/按钮可换中心，单击看详情。
- [ ] **4. 处理动态与窄屏。** Dashboard 首次唤醒、后续短聚焦、推荐淡入；sidebar 短过渡和下方滚动详情。只维护一个 rAF，inactive/hidden 暂停，destroy 清理；live reduced-motion 禁用运动/光波而不隐藏状态。所有控制可键盘使用，Esc 先关详情再返回；不要让标签移动影响命中位置。
- [ ] **5. 验证并提交。** 构建后 `node scripts/test_focus_view_browser.mjs` 和 `node --test extension/tests/focus-i18n.test.js` 通过，覆盖初次/重复进入、语言和状态 update、不重定位、32+候选分页、同坐标选择、reduced motion、两种 presentation 与销毁；`feat: add semantic Focus scene with adapted galaxy motion`。

## Task 6: Map 工作区集成与跨窗口回归

**Interfaces:**
- `createFocusSession({request,cancel,onChange,maxEntries=20}) -> {select(seedId,requestKey),load({refresh=false}),invalidate(),getSnapshot(),destroy()}`；request 为 `(seedId,{requestId}) -> Promise<FocusEnvelope>`。选择只读取缓存/本地状态，不请求；load 仅由显式按钮调用。内部递增 requestId，旧结果不能覆盖新选择。
- Session snapshot 为 `{seedId,requestKey,status,error,envelope}`，envelope 可为 null；workspace 合并本地近邻、envelope 候选及 suppressed，经 `projectFocus` 生成 scene snapshot 的 nodes。只在中心或请求键改变时 select，不在每次 UI update 重置会话。
- `createMapWorkspace({catalog,layout,state,language,presentation,viewState,requestFocus,cancelFocus,onSave,onDismiss,onSearch}) -> {element,update({state,language}),setActive(active),getViewState(),invalidateFocus(),destroy()}`。Map 子视图、临时中心、两套相机与一次性动画标记都在此窗口内；request results 属于 Focus session。

- [ ] **1. 写失败测试。** 新增 `focus-session.test.js`，扩展 dashboard/core/UI 浏览器测试。验证 maxEntries=20 的 LRU、同键复用、手动刷新、旧响应丢弃、全部失效、窗口独立和进入 Focus 零上传。

```js
session.select('A',keyA); assert.equal(sent.length,0);
const pending=session.load(); session.select('B',keyB);
resolveA(validA); await pending; assert.equal(session.getSnapshot().seedId,'B');
session.invalidate(); assert.equal(session.getSnapshot().status,'local');
```

- [ ] **2. 保留 Map 实例。** `app.js` 重绘外壳前暂时摘下 workspace.element，随后重新挂到 Map host；使用 update，不销毁重建地图。离开 Map 时暂停，返回复用；reset/pagehide 清理。状态更新仍保留原 settings 草稿、分页和焦点恢复。未保存星体也能进入 Focus；删去 Map 对旧 `focusMapTopic` 持久动作的依赖，Discover 自身行为保持原样。
- [ ] **3. 完成连接。** 接入 Galaxy/Focus 切换、进入中心优先级和返回快照；接入 Task 3 port、invalidated 通知、设置开关、中英文披露。缓存键包含规范化 endpoint、窗口内授权代次、推荐/schema 版本、source identity、seedId、options；不将密钥明文放入键或日志。endpoint/token/参数改变、reset、port 断开及失效通知清空相关缓存。保存兴趣不改变临时中心。
- [ ] **4. 预览与真实 API 测试。** 两个 HTML 入口加载 focus.css。`dev-preview.js` 保持明确示例标记和零隐式外网；无真实 Focus 服务时只展示公开的真实近邻并明确说明。回归中的 Focus POST 对接真正本地 API，使用合成个人状态；另外生成供预览使用、带来源身份与说明的真实公开 Focus 结果 fixture，不能沿用旧预览中虚构的 .3 距离。
- [ ] **5. 跑绿。** `npm test`、构建后 `npm run test:ui`、`npm run test:galaxy`、`npm run test:browser`。更新两份旧脚本中“Map focus 跳到 Discover”的断言，但保留正式 Discover focus 的覆盖。新增新接口认证、无隐式请求、侧栏/Dashboard 同步及并行请求检查；单击测试等待状态而不是原 80ms sleep。
- [ ] **6. 提交。** `feat: integrate Galaxy and Focus without rebuilding map state`。

## Task 7: 整体验证与本地交付

**Files:** `package.json`, `extension/manifest.json`, `docs/extension-guide.md`, 新增 `docs/focus-exploration-verification.md`；必要时更新 `tests/test_extension_build.py` 的资源/版本检查。

- [ ] **1. 冻结构建并跑测试。** 版本同步为 `0.1.4`；运行以下命令，失败时只针对相关变更修复，不把预期数字当作通过证据。Node 命令使用已验证的 Node 24。

```sh
export PATH="/Users/arthurfu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
.venv/bin/python -m pytest -q
npm test
npm run build
npm run test:ui
npm run test:browser
npm run test:galaxy
node scripts/test_galaxy_interactions_browser.mjs
node scripts/test_focus_view_browser.mjs
OTHERWISE_RUN_REAL_FOCUS=1 .venv/bin/python -m pytest -q tests/test_focus_service.py -k real_catalog
git diff --check
```

在 Task 1 新增 opt-in `test_real_catalog_focus_matches_packaged_identity`，上面的环境变量启用它：加载已有 MPNet cache、核对打包身份与实际角距离，不调用新模型编码。浏览器脚本可沿用 `OTHERWISE_PLAYWRIGHT_MODULE`、`OTHERWISE_CHROMIUM` 环境覆盖；真实服务使用离线缓存与临时 token。
- [ ] **2. 实际交互与截图。** 使用当前可用的 CUA 浏览器工具检查桌面 1440×900、Dashboard 390/320px、产品 sidepanel.html 390×850 和 320×850。检查单击、双击、触屏等效按钮、灰色点、领域筛选、搜索/保存/移除、分页、返回快照、pan/pinch/zoom、错误重试、快速换中心、live reduced motion 和详情滚动。修正原 gestures helper 自动把高度改为1000的问题。浏览器标签页中的 sidepanel.html 不冒充 Chrome 原生侧栏容器验证；无法实测的项目明确记录。
- [ ] **3. 独立审查。** 对相对于 `7ab7990` 的最终产品 diff 做一次独立审查，重点检查请求/权限边界、状态污染、实际动画生命周期、版本/ID/距离一致性。修复发现并仅重跑受影响检查及必要的最终构建。
- [ ] **4. 记录证据。** 在验证文档记录实际测试结果、截图位置、真实/示例数据边界、现存限制和迁移来源。保留可打开的产品预览；不要把队友原始 demo 当成最终成品。说明 Focus 仍不支持指定终点、中文推荐或知识掌握证明。
- [ ] **5. 交付到原安装位置。** 先备份 `/Users/arthurfu/Documents/OtherWise/dist/otherwise-extension` 与 ZIP 到该 checkout 的 `.cache/extension-build-backups/<timestamp>/`；再复制经过验证的产品构建，逐文件校验。只更新 ignored 构建产物，不切换原 checkout、不读取或修改 Chrome 存储、不用自动化操作 chrome://extensions。
- [ ] **6. 提交最终来源变更。** `feat: release semantic Focus and exploration mode locally`；报告 commit、预览、安装目录、测试和限制，不 push。如外部条件阻止某项验证，交付可用部分并明确尚未验证的边界，不能宣称全部通过。

## Execution preflight and handoff

执行时先再次确认目标分支和 dirty files；保留其他 agent 工作。使用现有 worktree，不另建线程或切换主目录。仅运行范围内的安装/构建步骤，不升级无关依赖。

建议采用 subagent-driven：协议和纯几何可并行，随后按依赖集成；每项完成后由独立 reviewer 检查，再做全分支审查。也可采用 native，由主 agent 逐项实现，最后独立审查一次。用户审阅本计划并选择执行方式之后才开始产品代码修改。
