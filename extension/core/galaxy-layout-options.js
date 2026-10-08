/** B controls change public map geometry, never recommendation distances. */
export const GALAXY_LAYOUT_DEFAULTS = Object.freeze({n_neighbors:12,min_dist:.4,spread:1.5,repulsion_strength:2.5});
export const GALAXY_LAYOUT_BOUNDS = Object.freeze({
  n_neighbors:{min:5,max:60,integer:true},min_dist:{min:0,max:1},spread:{min:.5,max:3},repulsion_strength:{min:.5,max:4},
});
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const keys=Object.keys(GALAXY_LAYOUT_DEFAULTS);
const valid=(key,value)=>typeof value==='number' && Number.isFinite(value) && value>=GALAXY_LAYOUT_BOUNDS[key].min && value<=GALAXY_LAYOUT_BOUNDS[key].max && (!GALAXY_LAYOUT_BOUNDS[key].integer || Number.isSafeInteger(value));
export function normalizeGalaxyLayoutOptions(raw,{strict=false}={}) {
  if(strict && (!object(raw) || Object.keys(raw).length!==keys.length || keys.some(key=>!Object.hasOwn(raw,key) || !valid(key,raw[key])) || raw.min_dist>raw.spread)) {
    throw new Error('Enter valid Galaxy layout settings. Minimum distance must not exceed spread.');
  }
  const result=Object.fromEntries(keys.map(key=>[key,object(raw) && valid(key,raw[key])?raw[key]:GALAXY_LAYOUT_DEFAULTS[key]]));
  if(result.min_dist>result.spread) result.min_dist=GALAXY_LAYOUT_DEFAULTS.min_dist;
  return result;
}
