export const focusDictionaries = {
  en: {
    back:'Back to Galaxy',center:'Focus center',chooseCenter:'Choose a center',searchPlaceholder:'Find any catalog topic',
    reset:'Reset view',zoomIn:'Zoom in',zoomOut:'Zoom out',getIdeas:'Get ideas',
    disclosure:'Get ideas sends only the selected catalog topic ID, public data version and seven numeric recommendation parameters. Entering Focus sends nothing.',
    local:'Your nearest topics are ready. Get ideas to discover more.',loading:'Looking for ideas…',
    ready:'Recommendations are ready.',error:'Recommendations are unavailable. Your nearest topics still work. Try Get ideas again.',
    empty:'No candidates in this distance band. Your nearest topics are still here.',
    neighbors:'Nearest topics',candidates:'Recommendations',distance:'Angular distance from center',
    geometry:'Radius shows measured similarity in the original 768-dimensional vectors. Direction comes from the global map; distances between surrounding stars are not semantic distances.',
    save:'Save interest',saved:'Saved interest',saving:'Saving…',dismiss:'Dismiss recommendation',explore:'Explore from here',
    google:'Search Google',youtube:'Search YouTube',closeDetails:'Close topic details',previous:'Previous',next:'Next',
    page:'Page {page} of {pages} · {count} candidates',selectionHelp:'Choose a star or a topic below. Double-click a star to change center.',
    canvas:'Semantic Focus map. Arrow keys pan, plus and minus zoom, Home resets. Topic lists provide selection for overlapping stars.',
    current:'Current center',actionError:'This action could not be completed. Please try again.',selected:'Selected {topic}.',domain:'Subject area',
  },
  'zh-CN': {
    back:'返回星图',center:'探索中心',chooseCenter:'选择中心',searchPlaceholder:'查找任意目录主题',
    reset:'重置视图',zoomIn:'放大',zoomOut:'缩小',getIdeas:'获取推荐',
    disclosure:'点击获取推荐时，仅发送所选目录主题 ID、公开数据版本和七项数值推荐参数。进入聚焦探索不会发送数据。',local:'最近主题已就绪。点击获取推荐，探索更多主题。',loading:'正在查找推荐…',
    ready:'推荐已就绪。',error:'暂时无法获取推荐，最近主题仍然可用。可再次点击获取推荐重试。',
    empty:'该距离范围内没有候选主题，最近主题仍然可用。',
    neighbors:'最近主题',candidates:'推荐主题',distance:'与中心的角距离',
    geometry:'半径表示原始 768 维向量中的相似度，方向来自全局星图；周围星体之间的屏幕距离不代表语义距离。',
    save:'保存兴趣',saved:'已保存的兴趣',saving:'保存中…',dismiss:'忽略推荐',explore:'从这里探索',
    google:'在 Google 搜索',youtube:'在 YouTube 搜索',closeDetails:'关闭主题详情',previous:'上一页',next:'下一页',
    page:'第 {page} / {pages} 页 · {count} 个候选主题',selectionHelp:'选择星体或下方主题查看详情，双击星体可更换中心。',
    canvas:'语义探索地图。方向键平移，加减键缩放，Home 键重置。重合星体可通过主题列表选择。',
    current:'当前中心',actionError:'未能完成此操作，请重试。',selected:'已选择 {topic}。',domain:'学科领域',
  },
};
export function focusText(language,key,values={}) {
  const text=(focusDictionaries[language] || focusDictionaries.en)[key] || key;
  return text.replace(/\{(\w+)\}/g,(_,name)=>String(values[name] ?? ''));
}
