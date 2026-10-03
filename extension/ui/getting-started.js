export function gettingStartedGuide({text, step, busy, seen, error}) {
  const disabled = busy ? ' disabled' : '';
  return `<dialog class="welcome-guide" id="welcome-guide" aria-labelledby="guide-heading" aria-describedby="guide-body">
    <div class="guide-progress"><p class="eyebrow">${text('guideStep',{step:step+1,total:3})}</p><div class="guide-dots" aria-hidden="true">${[0,1,2].map(index=>`<span${index===step?' class="is-current"':''}></span>`).join('')}</div></div>
    <h2 id="guide-heading">${text(`guideHeading_${step}`)}</h2><p id="guide-body">${text(`guideBody_${step}`)}</p>
    <p class="muted small">${text('guidePrivacy')}</p>${error?`<p role="alert">${text('guideSaveError')}</p>`:''}
    <div class="guide-actions"><button type="button" class="quiet" data-guide-action="skip" data-focus="guide-skip"${disabled}>${text(seen?'guideClose':'guideSkip')}</button>${step>0?`<button type="button" data-guide-action="back" data-focus="guide-back"${disabled}>${text('guideBack')}</button>`:''}<button type="button" class="primary" data-guide-action="${step===2?'start':'next'}" data-focus="guide-next" autofocus${disabled}>${text(busy?'saving':step===2?(seen?'guideStartExisting':'guideStart'):'guideNext')}</button></div>
  </dialog>`;
}
