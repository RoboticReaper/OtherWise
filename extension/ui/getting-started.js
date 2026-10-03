export function gettingStartedGuide({text, view, step, total, busy, seen, error}) {
  const disabled = busy ? ' disabled' : '';
  return `<aside class="welcome-guide" id="welcome-guide" aria-labelledby="guide-heading" aria-describedby="guide-body">
    <div class="guide-progress"><p class="eyebrow">${text('guideStep',{step:step+1,total})}</p><div class="guide-dots" aria-hidden="true">${Array.from({length:total},(_,index)=>`<span${index===step?' class="is-current"':''}></span>`).join('')}</div></div>
    <p class="guide-page">${text(view)}</p><h2 id="guide-heading" data-focus="guide-heading" tabindex="-1">${text(`guideHeading_${view}`)}</h2><p id="guide-body">${text(`guideBody_${view}`)}</p>
    <p class="muted small">${text('guidePrivacy')}</p>${error?`<p role="alert">${text('guideSaveError')}</p>`:''}
    <div class="guide-actions"><button type="button" class="quiet" data-guide-action="skip" data-focus="guide-skip"${disabled}>${text(seen?'guideClose':'guideSkip')}</button>${step>0?`<button type="button" data-guide-action="back" data-focus="guide-back"${disabled}>${text('guideBack')}</button>`:''}<button type="button" class="primary" data-guide-action="${step===total-1?'finish':'next'}" data-focus="guide-next"${disabled}>${text(busy?'saving':step===total-1?'guideFinish':'guideNext')}</button></div>
  </aside>`;
}
