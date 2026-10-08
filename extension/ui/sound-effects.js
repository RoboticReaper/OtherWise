import {explorationSets} from './exploration-logic.js';

const sources = Object.fromEntries(['save', 'explore', 'bloom'].map(kind => [kind, new URL(`../assets/sounds/${kind}.wav`, import.meta.url).href]));
const cooldownMs = 2_000;
const list = value => Array.isArray(value) ? value : [];
const id = topic => topic?.id || topic?.topic;
const volume = settings => typeof settings?.soundEffectsVolume === 'number' && Number.isFinite(settings.soundEffectsVolume)
  ? Math.max(0, Math.min(1, settings.soundEffectsVolume)) : .2;

/** One foreground window owns its sounds; state subscriptions never trigger playback. */
export function createSoundEffects({getSettings = () => ({}), clock = () => performance.now(),
  isActive = () => document.visibilityState === 'visible' && document.hasFocus(), isCurrentFocus = () => true,
  createAudio = url => new Audio(url), schedule = setTimeout, cancel = clearTimeout} = {}) {
  let lastPlayed = -Infinity;
  let pending = null, media = null, sequence = 0;

  function cancelPending() {if (pending !== null) cancel(pending); pending = null;}
  function stop() {
    cancelPending(); sequence++;
    const previous = media; media = null;
    try {previous?.pause();} catch { /* Optional audio must never interrupt the app. */ }
  }
  function allowed(now) {
    return getSettings()?.soundEffectsEnabled === true && volume(getSettings()) > 0 && isActive()
      && now - lastPlayed >= cooldownMs;
  }
  async function play(kind) {
    if (!sources[kind] || !isActive() || volume(getSettings()) === 0) return null;
    stop(); const token = sequence;
    try {
      const current = createAudio(sources[kind]); media = current;
      current.volume = volume(getSettings()); current.loop = false;
      current.onended = () => {if (media === current) media = null;};
      await current.play();
      return token === sequence ? kind : null;
    } catch {
      if (token === sequence) stop();
      return null;
    }
  }
  async function saved(before, after, {data, mapVisible = false, actionToken = sequence} = {}) {
    if (actionToken !== sequence || !before || !after || after.lastError || before.salt !== after.salt) return null;
    const previous = new Set(list(before.approved).map(id));
    if (!list(after.approved).some(topic => id(topic) && !previous.has(id(topic)))) return null;
    const now = clock();
    if (!allowed(now)) return null;
    let kind = 'save';
    if (mapVisible && after.settings?.galaxyExplorationMode === true && data) {
      const oldLights = explorationSets(data, before).lit;
      const newLights = [...explorationSets(data, after).lit].filter(topic => !oldLights.has(topic));
      if (newLights.length >= 5) kind = 'bloom';
    }
    lastPlayed = now;
    return play(kind);
  }
  function enterFocus(topic) {
    stop();
    if (!topic?.id) return;
    pending = schedule(() => {
      pending = null;
      const now = clock();
      if (!isCurrentFocus(topic.id) || !allowed(now)) return;
      lastPlayed = now;
      void play('explore');
    }, 450);
  }
  function syncSettings() {
    if (getSettings()?.soundEffectsEnabled !== true || volume(getSettings()) === 0) stop();
    else if (media) media.volume = volume(getSettings());
  }
  function reset() {stop(); lastPlayed = -Infinity;}
  return {saved, enterFocus, preview: play, stop, syncSettings, reset, captureAction: () => sequence};
}
