const copy={
 galaxy:['Galaxy','星图'],focus:['Focus','聚焦探索'],views:['Map views','地图视图'],refresh:['Refresh ideas','刷新推荐'],settings:['Open Settings','打开设置'],
 unconfigured:['Set up the service address and team access code in Settings. Your local neighbors remain available.','请在设置中填写服务地址和团队访问码。本地近邻仍可查看。'],
 permission:['Check the access code and save the connection in Settings to allow this service. Local neighbors remain available.','请在设置中检查访问码，并保存连接以授权此服务。本地近邻仍可查看。'],
 timeout:['The request took too long. Try Get ideas again; local neighbors are still available.','请求超时。请重新获取推荐；本地近邻仍可查看。'],
 version:['The service and local Galaxy use different data versions. Update the data before retrying. Local neighbors remain available.','服务与本地星图的数据版本不一致。请更新数据后重试。本地近邻仍可查看。'],
 unavailable:['Focus ideas are unavailable. Check the connection in Settings and try again. Local neighbors remain available.','聚焦推荐暂不可用。请在设置中检查连接后重试。本地近邻仍可查看。'],
 preview:['This offline example has no recorded Focus batch for this topic and settings. These neighbors come from the real public catalog.','此离线示例没有该主题与参数的聚焦推荐记录。当前近邻来自真实公开目录。'],
 previewNote:['Offline example: only packaged public catalog data is used. Get ideas opens a recorded real batch when available; no service request is sent.','离线示例：仅使用打包的公开目录数据。获取推荐时会显示已有的真实推荐记录（若有）；不会请求服务。'],
};
export function workspaceText(language,key){return copy[key]?.[language==='zh-CN'?1:0]||key;}
