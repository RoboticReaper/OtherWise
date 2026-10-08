import {createBackup, parseBackup, MAX_BACKUP_BYTES} from '../core/backup.js';

const copy = {
  title:['Import & export','导入与导出'],
  help:['Back up saved interests, exploration paths, concept feedback and preferences as a JSON file.','将已保存的兴趣、探索路径、概念反馈和偏好备份为 JSON 文件。'],
  privacy:['Backups stay on your device and contain personal interests. Access codes, service addresses, browsing evidence and temporary recommendations are excluded. Import never enables browsing access.','备份保存在你的设备上，包含个人兴趣。不包含访问码、服务地址、浏览记录依据或临时推荐。导入不会开启浏览记录权限。'],
  export:['Export backup','导出备份'], import:['Import backup','导入备份'],
  draft:['Save your settings changes before importing. Export includes saved settings only.','请先保存设置修改再导入。导出仅包含已保存的设置。'],
  review:['Review backup','确认备份内容'], date:['Exported','导出时间'],
  interests:['Saved interests','已保存的兴趣'], paths:['Exploration records','探索记录'], ratings:['Concept ratings','概念反馈'],
  merge:['Merge with this device','与本机数据合并'],
  mergeHelp:['Add missing records. Keep local preferences and existing ratings. Reimporting the same file does not duplicate records.','添加缺少的记录，保留本机偏好和已有反馈。重复导入同一文件不会增加重复记录。'],
  replace:['Replace saved data & preferences','替换保存的数据与偏好'],
  replaceHelp:['Restore the backup’s interests, paths, feedback and preferences. Local connection settings stay on this device. Restored website exclusions also apply to local browsing data. Export your current data first if you want to keep it.','恢复备份中的兴趣、路径、反馈和偏好。本机连接设置会保留，恢复的网站排除规则也会应用于本机浏览数据。如需保留当前数据，请先导出备份。'],
  acknowledge:['I understand that the current saved data and preferences will be replaced.','我理解当前保存的数据与偏好将被替换。'],
  cancel:['Cancel','取消'], confirm:['Import backup','导入备份'], importing:['Importing…','正在导入…'],
  invalid:['This is not a valid OtherWise backup.','这不是有效的 OtherWise 备份。'],
  version:['This backup version is not supported. Update OtherWise and try again.','暂不支持此备份版本，请更新 OtherWise 后重试。'],
  size:['Choose an OtherWise JSON backup smaller than 5 MB.','请选择小于 5 MB 的 OtherWise JSON 备份。'],
  overflow:['This import would exceed 40 saved interests. Remove some interests or choose Replace.','导入后会超过 40 个兴趣，请先移除一些兴趣，或选择替换。'],
  limits:['This import would exceed the backup data limits. Choose Replace or use a smaller backup.','导入后会超过备份数据上限，请选择替换或使用较小的备份。'],
  failure:['Could not import the backup. Please try again.','无法导入备份，请重试。'],
};
export const backupText = (language,key) => copy[key][language === 'zh-CN' ? 1 : 0];
export function backupSettingsView(language, dirty, pending) {
  const t = key => backupText(language,key);
  return `<p class="muted small">${t('help')}</p><div class="data-actions"><button type="button" data-action="backup-export" data-focus="backup-export"${pending ? ' disabled' : ''}>${t('export')}</button><button type="button" data-action="backup-import" data-focus="backup-import"${pending || dirty ? ' disabled' : ''}>${t('import')}</button><input type="file" id="backup-file" accept=".json,application/json" hidden></div><p class="muted small" id="backup-draft-note" role="status"${dirty ? '' : ' hidden'}>${t('draft')}</p><p class="privacy-note">${t('privacy')}</p>`;
}
export function downloadBackup(state) {
  const backup = createBackup(state);
  const url = URL.createObjectURL(new Blob([JSON.stringify(backup)],{type:'application/json'}));
  const link = document.createElement('a');
  link.href = url; link.download = `OtherWise-backup-${backup.exportedAt.replace(/[:.]/g,'-')}.json`;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export async function readBackupFile(file) {
  if (!file || file.size > MAX_BACKUP_BYTES) throw new Error(copy.size[0]);
  return parseBackup(await file.text());
}
export function backupError(language,error) {
  const message = error?.message;
  const found = Object.values(copy).find(values => values[0] === message);
  return found?.[language === 'zh-CN' ? 1 : 0] || backupText(language,'failure');
}
export function reviewBackup({backup,language,onImport,onExport}) {
  const t = key => backupText(language,key), dialog = document.createElement('dialog');
  dialog.className = 'backup-dialog';
  dialog.setAttribute('aria-labelledby','backup-title');
  // Only validated counts and a formatted date enter this markup.
  const data = backup.data;
  dialog.innerHTML = `<form><h2 id="backup-title">${t('review')}</h2><p class="muted small">${t('date')}: ${new Date(backup.exportedAt).toLocaleString(language === 'zh-CN' ? 'zh-CN' : 'en-US')}</p><dl class="backup-summary">${[['interests',data.approved.length],['paths',data.explored.length],['ratings',Object.keys(data.discovery.feedback).length]].map(([key,count]) => `<div><dt>${t(key)}</dt><dd>${count}</dd></div>`).join('')}</dl><fieldset class="backup-modes"><legend>${t('import')}</legend><label><input type="radio" name="backup-mode" value="merge" checked autofocus><strong>${t('merge')}</strong><small>${t('mergeHelp')}</small></label><label><input type="radio" name="backup-mode" value="replace"><strong>${t('replace')}</strong><small>${t('replaceHelp')}</small></label></fieldset><label class="backup-ack" hidden><input type="checkbox" id="backup-ack"><span>${t('acknowledge')}</span></label><p class="backup-error" role="alert" hidden></p><div class="dialog-actions"><button type="button" data-backup-export>${t('export')}</button><button type="button" data-backup-cancel>${t('cancel')}</button><button type="submit" class="primary">${t('confirm')}</button></div></form>`;
  let pending = false;
  const errorNode = dialog.querySelector('.backup-error'), submit = dialog.querySelector('[type="submit"]');
  const showError = error => {errorNode.textContent = backupError(language,error);errorNode.hidden = false;};
  const refresh = () => {
    const replace = dialog.querySelector('[name="backup-mode"]:checked').value === 'replace';
    dialog.querySelector('.backup-ack').hidden = !replace;
    submit.disabled = pending || replace && !dialog.querySelector('#backup-ack').checked;
    errorNode.hidden = true;
  };
  dialog.addEventListener('change',refresh);
  dialog.querySelector('[data-backup-cancel]').onclick = () => dialog.close();
  dialog.querySelector('[data-backup-export]').onclick = async () => {try {await onExport();} catch(error) {showError(error);}};
  dialog.querySelector('form').onsubmit = async event => {
    event.preventDefault(); if (pending || submit.disabled) return;
    pending = true;
    dialog.querySelectorAll('input,button').forEach(node => node.disabled = true);
    submit.textContent = t('importing');
    try {await onImport(backup,dialog.querySelector('[name="backup-mode"]:checked').value);dialog.close();}
    catch(error) {
      pending = false;dialog.querySelectorAll('input,button').forEach(node => node.disabled = false);
      submit.textContent = t('confirm');refresh();showError(error);
    }
  };
  dialog.addEventListener('cancel',event => {if (pending) event.preventDefault();});
  dialog.addEventListener('close',() => {dialog.remove();document.querySelector('[data-focus="backup-import"]')?.focus();},{once:true});
  document.body.append(dialog);dialog.showModal();
}
