/** Native fullscreen keeps the map and its controls together in the top layer. */
export function createMapFullscreen({surface, button, text, onResize}) {
  const document = surface.ownerDocument;
  let destroyed = false, pending = false, active = true;
  const error = document.createElement('p');
  error.className = 'map-fullscreen-error'; error.setAttribute('role', 'alert'); error.hidden = true;
  surface.append(error);
  const isFullscreen = () => document.fullscreenElement === surface;
  function update() {
    if (destroyed) return;
    button.textContent = text(isFullscreen() ? 'exitFullscreen' : 'fullscreen');
    button.setAttribute('aria-pressed', String(isFullscreen()));
    button.title = button.textContent;
    if (!error.hidden) error.textContent = text('fullscreenUnavailable');
  }
  function changed() { update(); if (!destroyed) onResize(); }
  async function toggle() {
    if (destroyed || pending || !active) return;
    pending = true; error.hidden = true;
    try {
      if (isFullscreen()) await document.exitFullscreen();
      else { await surface.requestFullscreen(); if (destroyed || !active) exit(); }
    } catch {
      if (!destroyed) { error.textContent = text('fullscreenUnavailable'); error.hidden = false; }
    } finally { pending = false; update(); }
  }
  function exit() { if (isFullscreen()) document.exitFullscreen().catch(() => {}); }
  function keydown(event) {
    if (event.key === 'Escape' && isFullscreen()) {
      event.preventDefault(); event.stopPropagation(); exit();
    }
  }
  document.addEventListener('fullscreenchange', changed);
  document.addEventListener('keydown', keydown, true);
  update();
  return {toggle, update, setActive(value) { active = Boolean(value); if (!active) exit(); }, destroy() {
    destroyed = true; exit(); document.removeEventListener('fullscreenchange', changed);
    document.removeEventListener('keydown', keydown, true); error.remove();
  }};
}
