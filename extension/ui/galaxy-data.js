// This loader reads only packaged public assets. It never sends local interests.
export function createGalaxyLoader({fetchImpl = globalThis.fetch} = {}) {
  let pending;
  return {
    invalidate() { pending = null; },
    load() {
      if (!pending) pending = Promise.all(['catalog.json', 'galaxy-layout.json'].map(async file => {
        const response = await fetchImpl(new URL(`../${file}`, import.meta.url), {credentials: 'omit', redirect: 'error'});
        if (!response.ok) throw new Error('Galaxy assets are unavailable.');
        return response.json();
      })).then(([catalog, layout]) => ({catalog, layout})).catch(() => {
        pending = null;
        throw new Error('Galaxy assets are unavailable.');
      });
      return pending;
    },
  };
}

export const galaxyLoader = createGalaxyLoader();
