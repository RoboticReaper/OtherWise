# Focus animation provenance

The Focus scene selectively adapts rendering primitives from [BowenX307/otherwise](https://github.com/BowenX307/otherwise), commit `8281161`, inspected in the read-only local checkout `/private/tmp/otherwise-teammate-review.r8IPzY`.

| Product module | Source | Retained behavior | Product adaptation |
| --- | --- | --- | --- |
| `extension/ui/focus-orb.js` | `src/universe/orbCore.ts` | Two-part orb, flared slit mask, rounding filter, breathing, looking, reading, gather/release states, squeeze interpolation and nearest equivalent slit angle | Build-free JavaScript, injected domain color, per-scene SVG ID prefix, explicit caller clock, immediate static state under reduced motion |
| `extension/ui/focus-stars.js` | `src/universe/starfield.ts` | Three depths of sparse stars, seeded positions, tiling, subtle twinkle/parallax and a passing wave's brightness boost | Independent deterministic generator, explicit time/motion/view arguments, compact sidebar counts, no simulation/engine import |
| `extension/ui/focus.js` | Visual sequence reference: `src/universe/UniverseScene.tsx` | Orb gathers, opens and releases an expanding wave on the first dashboard entry; subsequent entries and center changes use a short fade | New scene implementation, one animation loop, fixed semantic nodes supplied by `projectFocus`, circular measured-distance guides, existing product actions and pagination |

The source orb module itself notes an earlier origin in `productspace/app/renderer/orb-mark.js`; that attribution is preserved here. No React page, teammate mock API, physical simulation, orbital slots, decorative three-orbit layout, continuing orbit motion or teammate personal data is copied.

Focus circles are labeled angular distances (`0.10`, `0.20`, `0.30`) in the existing 768-dimensional embedding space. Star positions are provided by the approved semantic projection; animation changes opacity and the orb/background, never node geometry. A new recommendation batch does not move the camera. The first wake lasts about 1.1 seconds; repeated dashboard entries fade for 0.35 seconds and sidebar entries for 0.18 seconds. Reduced motion disables these fades, wave, parallax, twinkle and orb breathing immediately, including live preference changes.

The scene fetches nothing and stores nothing. Its callbacks hand explicit actions to the product owner; its returned view state is temporary per-window presentation state. Browser verification uses synthetic catalog/state fixtures in an isolated loopback page. Those recommendations validate presentation and are not represented as results from the real Focus API.
