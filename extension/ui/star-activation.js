/** Own the short, cancelable detail-selection window independently of pointer input. */
export function createStarActivation({onSelect, onEnterFocus, delay = 250, schedule = setTimeout, cancelTimer = clearTimeout} = {}) {
  let timer = null, destroyed = false;
  function cancel() {
    if (timer !== null) cancelTimer(timer);
    timer = null;
  }
  return {
    click(id) {
      if (destroyed) return;
      cancel();
      timer = schedule(() => { timer = null; if (!destroyed) onSelect?.(id); }, delay);
    },
    doubleClick(id) {
      if (destroyed) return;
      cancel(); onEnterFocus?.(id);
    },
    cancel,
    destroy() { cancel(); destroyed = true; },
  };
}
