# Batch 004 independent initial audit

Frozen revision: 3. Candidate SHA-256: `1d02d5e1e05532db9b7dc65c2aefd68c715e738e21539e9f8da306a7069fc2a5`.
Initial findings frozen: 2026-10-08T22:21:14.815169+00:00. Final acceptance belongs to the coordinator.

## Scope and result

- 20/20 prescribed random-new cards: no substantive findings.
- 20/20 disjoint risk-selected cards: one medium evidence/takeaway finding.
- 57/57 additional targeted IDs: no additional substantive findings.
- All 76 changed bundles checked independently: 19 overlap the fixed sample, 57 are additional.
- Recomputed change inventory: 63 card-text changes, 6 relationship bundles, 8 source records (7 modified, 1 added).
- 94 attached relationships checked; all targets resolve and assertion/type choices are supported.
- 99 cited public originals inspected. Sampling, snapshots, candidate/baseline/selection hashes, identity ownership and 30–50-word lengths verify.

## Required correction

1. **b004-f01, medium, risk sample: Graph theory (local:authored:000604).** The learning takeaway mentions bipartite colorability, but the attached m18 and m21 evidence covers the field definition and adjacency-matrix representations. Align the takeaway with that lesson, or explicitly attach the existing m20 two-colorability passage and reconcile the teaching focus. The prose and relationship are supported. Preserve this finding and recheck the revised bundle separately.

## Scope and access limits

The random and risk findings are separate; no pooled defect estimate is appropriate. The additional group is targeted correction coverage. Three extra IDs are reference-metadata-only: Henderson–Hasselbalch equation, Second moment of area, and Euler column buckling. Their shared source correction was checked once and their unchanged claims/relationships plus version increment were verified; they do not add full factual-audit coverage. Four other reference-only bundles are in the fixed sample and received the full sample audit.

No live public URL failed. The web tool may return indexed crawl content. Original raw acquisition bytes are missing for 31 references, so their original acquisition hashes cannot be recomputed; they match retained extracted-source metadata and live support was independently checked. This is a provenance-retention limitation, not proof of absent browsing or unsupported claims.

## Individual records

### Random walk · local:catalog:random-walk
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The restrictions, dimensions and lattice distinctions are directly supported. The related Markov-chain passage explicitly uses a simple random walk as an example without claiming every restricted walk is Markov.
Sources: [m53](https://mathworld.wolfram.com/RandomWalk.html) (Random Walk -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Gambler’s ruin · local:catalog:gamblers-ruin
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Independent fair unit steps and finite bankrolls bound the absorption claim. The smaller-bankroll probability follows the displayed ratio; the random-walk application is correctly editorial.
Sources: [m52](https://mathworld.wolfram.com/GamblersRuin.html) (Gambler's Ruin -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Triple point · local:catalog:triple-point
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Water coexistence and sub-triple-pressure exclusion match the phase-diagram passage. Pure-substance/equilibrium bounds remain. The added evidence and editorial comparison correctly distinguish triple from critical points.
Sources: [c12](https://openstax.org/books/chemistry-2e/pages/10-4-phase-diagrams) (10.4 Phase Diagrams; inspected passage indices 12, 25, 40 (zero-based in saved snapshot); HTML anchors: fs-idm105744432; fs-idm71881152; fs-idm114606944)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Critical damping · local:catalog:critical-damping
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The linear spring-mass/released-from-rest conditions appropriately bound fastest nonoscillatory return. The source contrasts underdamped, critical and overdamped regimes. Shared-locator change does not alter the current qualified prose.
Sources: [p08](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations) (15.5 Damped Oscillations; inspected passage indices 18, 19 (zero-based in saved snapshot); HTML anchors: fs-id1167131215180; fs-id1167131503759)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Damped harmonic motion · local:catalog:damped-harmonic-motion
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Weak damping, velocity-proportional opposing force and exponential envelope all match the source model; no universal damping law is asserted. Shared p08 correction adds coverage without changing this card or relation.
Sources: [p08](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations) (15.5 Damped Oscillations; inspected passage indices 7, 9, 10, 12 (zero-based in saved snapshot); HTML anchors: fs-id1167131080334; fs-id1167131181569; fs-id1167129966801; fs-id1167131498071)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Fracture toughness · local:catalog:fracture-toughness
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The source separates applied stress intensity from critical material resistance and explicitly includes crack geometry. Linear-elastic/appropriate-critical-value wording avoids endorsing every approximation in the source’s displayed toughness formula.
Sources: [e37](https://eng.libretexts.org/Courses/California_State_Polytechnic_University_Humboldt/Mechanical_Behavior_of_Material/Chapter_10%3A_Creep%2C_Fracture%2C_and_Fatigue) (Chapter 10: Creep, Fracture, and Fatigue; inspected passage indices 142, 143, 144, 145 (zero-based in saved snapshot); HTML anchors: paragraph-143; paragraph-144; paragraph-145; paragraph-146)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Torque-induced gyroscopic precession · local:catalog:torque-induced-gyroscopic-precession
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Perpendicular torque changes angular-momentum direction, and slow-precession/fast-spin assumptions are explicit. The limited facet is distinct from unrestricted precession and correctly linked to that broader identity.
Sources: [p04](https://openstax.org/books/university-physics-volume-1/pages/11-4-precession-of-a-gyroscope) (11.4 Precession of a Gyroscope; inspected passage indices 6, 7, 17 (zero-based in saved snapshot); HTML anchors: fs-id1165038331707; fs-id1165038198551; fs-id1165037997345)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Choosing a titration indicator · local:catalog:choosing-a-titration-indicator
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The strong/weak acid examples support the early-endpoint warning. The correction now says an unsuitable indicator can fail rather than treating every indicator as interchangeable.
Sources: [c15](https://openstax.org/books/chemistry-2e/pages/14-7-acid-base-titrations) (14.7 Acid-Base Titrations; inspected passage indices 54, 55 (zero-based in saved snapshot); HTML anchors: fs-idm188916592; fs-idm224614176)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Möbius inversion formula · local:catalog:mobius-inversion-formula
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Inspected equations (1) and (2), including image alt text, establish divisor summation and Möbius-weighted inversion. The sense is arithmetic inversion, not Möbius-strip topology.
Sources: [m32](https://mathworld.wolfram.com/MoebiusInversionFormula.html) (Möbius Inversion Formula -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### S–N curve · local:catalog:sn-curve
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The source supports cyclic stress amplitude, measured cycles to failure, and the material-specific endurance distinction. Its later mean-load discussion supports the service-loading caution.
Sources: [e38](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_of_Materials_(Roylance)/06%3A_Yield_and_Fracture/6.05%3A_Fatigue) (6.5: Fatigue; inspected passage indices 73, 74 (zero-based in saved snapshot); HTML anchors: section_2)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Poisson process · local:catalog:poisson-process
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The constant-rate qualification and small-interval asymptotic wording fit the source conditions. Random clusters are a permitted consequence, not a claim of dependence; exponential waiting-time linkage is explicit in m39.
Sources: [m48](https://mathworld.wolfram.com/PoissonProcess.html) (Poisson Process -- from Wolfram MathWorld; inspected passage indices 1, 2, 3, 4, 5 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4; paragraph-5; paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Thin-film interference · local:catalog:thin-film-interference
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Two reflected paths, index-dependent reflection phase and wavelength/thickness effects are supported. The optics bridge is editorial and does not imply an independently asserted hierarchy.
Sources: [p17](https://openstax.org/books/university-physics-volume-3/pages/3-4-interference-in-thin-films) (3.4 Interference in Thin Films; inspected passage indices 6, 8, 10, 11 (zero-based in saved snapshot); HTML anchors: fs-id1170903087288; fs-id1170902600773; fs-id1170903054004; fs-id1170902643736)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Geodesic · local:catalog:geodesic
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The Riemannian qualifier and local/global distinction fit the source. A great-circle arc continued beyond the shorter arc need not minimize globally. The bridge to topology remains editorial.
Sources: [m07](https://mathworld.wolfram.com/Geodesic.html) (Geodesic -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Neutral axis in beam bending · local:catalog:neutral-axis-in-beam-bending
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Simple elastic bending bounds the stress-sign change. The source explains tensile/compressive surfaces and failure locations; e40 explicitly uses distance from the neutral axis. Shared e39 correction leaves this card unchanged.
Sources: [e39](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_of_Materials_(Roylance)/04%3A_Bending/4.02%3A_Stresses_in_Beams) (4.2: Stresses in Beams; inspected passage indices 68, 70, 72 (zero-based in saved snapshot); HTML anchors: section_1; section_2)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Homogeneous catalysis · local:catalog:homogeneous-catalysis
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Same phase, intermediate formation and regeneration are explicit in the cited homogeneous-catalyst definition; the card avoids treating a catalyst as absent from individual steps.
Sources: [c09](https://openstax.org/books/chemistry-2e/pages/12-7-catalysis) (12.7 Catalysis; inspected passage indices 15, 20 (zero-based in saved snapshot); HTML anchors: fs-idm243256336; fs-idm251830192)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Critical point of a fluid · local:catalog:critical-point-of-a-fluid
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Coexistence termination and inability to liquefy above critical temperature are supported. The shared c12 locator revision leaves prose and relationship unchanged; source text also discusses dense supercritical fluid.
Sources: [c12](https://openstax.org/books/chemistry-2e/pages/10-4-phase-diagrams) (10.4 Phase Diagrams; inspected passage indices 40 (zero-based in saved snapshot); HTML anchors: fs-idm114606944)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Coriolis force · local:catalog:coriolis-force
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The rotating-frame account is contrasted with inertia in an inertial frame. The card does not invent a separate interaction or confuse the named Coriolis effect with all rotating-frame forces.
Sources: [p05](https://openstax.org/books/university-physics-volume-1/pages/6-3-centripetal-force) (6.3 Centripetal Force; inspected passage indices 44, 50 (zero-based in saved snapshot); HTML anchors: fs-id1165039268847; fs-id1165039316978)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Gravitational potential energy · local:catalog:gravitational-potential-energy
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The Newtonian bound and zero-at-infinity convention are explicit. The sign and separation trend agree with the derivation; constant-g height energy is correctly restricted to nearly uniform field.
Sources: [p06](https://openstax.org/books/university-physics-volume-1/pages/13-3-gravitational-potential-energy-and-total-energy) (13.3 Gravitational Potential Energy and Total Energy; inspected passage indices 8, 9, 12 (zero-based in saved snapshot); HTML anchors: fs-id1168329069323; fs-id1168326774371; fs-id1168329511648)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Chromatic polynomial · local:catalog:chromatic-polynomial
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Finite undirected graphs, distinguishable color labels and counting versus minimum-color distinction are supported. Bipartite two-colorability is independently supported by m20 for the editorial comparison.
Sources: [m27](https://mathworld.wolfram.com/ChromaticPolynomial.html) (Chromatic Polynomial -- from Wolfram MathWorld; inspected passage indices 1, 3, 13 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-4; paragraph-14)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Exponential distribution · local:catalog:exponential-distribution
Group: random_new. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The displayed density and memoryless statement support all claims. Positive constant rate appropriately bounds the waiting-time law and prevents zero-rate degeneracy.
Sources: [m39](https://mathworld.wolfram.com/ExponentialDistribution.html) (Exponential Distribution -- from Wolfram MathWorld; inspected passage indices 1, 2, 4 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-5)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Hubble Space Telescope · local:catalog:hubble-space-telescope
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The atmosphere passage explicitly names Hubble and changing refraction; the aperture passage supports remaining diffraction limits. The card avoids claiming infinite resolution or superiority to every ground telescope.
Sources: [p38](https://openstax.org/books/astronomy-2e/pages/6-2-telescopes-today) (6.2 Telescopes Today; inspected passage indices 37, 38, 40 (zero-based in saved snapshot); HTML anchors: fs-id1167471084189; fs-id1167470709434; fs-id1167470632380), [p15](https://openstax.org/books/university-physics-volume-3/pages/4-5-circular-apertures-and-resolution) (4.5 Circular Apertures and Resolution; inspected passage indices 8, 9, 11 (zero-based in saved snapshot); HTML anchors: fs-id1172101688448; fs-id1172101945964; fs-id1172099490776)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Creep (materials) · local:catalog:creep-materials
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Time, sustained loading, elevated-temperature metals/ceramics and turbine-blade relevance are supported. The editorial fatigue comparison distinguishes sustained from repeated loading without merging the senses.
Sources: [e37](https://eng.libretexts.org/Courses/California_State_Polytechnic_University_Humboldt/Mechanical_Behavior_of_Material/Chapter_10%3A_Creep%2C_Fracture%2C_and_Fatigue) (Chapter 10: Creep, Fracture, and Fatigue; inspected passage indices 68, 69, 71 (zero-based in saved snapshot); HTML anchors: paragraph-69; paragraph-70; paragraph-72)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Memoryless property · local:catalog:memoryless-property
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The conditional-survival equation and discrete/continuous examples support the qualified wording. It does not confuse memorylessness with complete absence of information or assert a single geometric counting convention.
Sources: [m38](https://mathworld.wolfram.com/Memoryless.html) (Memoryless -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3), [m39](https://mathworld.wolfram.com/ExponentialDistribution.html) (Exponential Distribution -- from Wolfram MathWorld; inspected passage indices 4 (zero-based in saved snapshot); HTML anchors: paragraph-5), [m40](https://mathworld.wolfram.com/GeometricDistribution.html) (Geometric Distribution -- from Wolfram MathWorld; inspected passage indices 3, 4 (zero-based in saved snapshot); HTML anchors: paragraph-4; paragraph-5)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Chemistry · local:authored:000624
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Macroscopic, microscopic and symbolic domains support the broad learning example. The modal wording does not assert every visible change must be chemical. No hierarchy is invented.
Sources: [c01](https://openstax.org/books/chemistry-2e/pages/1-1-chemistry-in-context) (1.1 Chemistry in Context; inspected passage indices 14, 19, 23 (zero-based in saved snapshot); HTML anchors: fs-idm183676832; fs-idm148555376; fs-idm166065136)
Relationships: 0 checked; see exact target/type/assertion records in audit.initial.json.

### Three-point bending test · local:catalog:three-point-bending-test
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The corrected slender/uniform/small-deflection/linear-elastic assumptions fit e39 and e42. The midpoint simply-supported formula directly gives the stated load, span-cubed and EI dependence; source and relationship additions are supported.
Sources: [e42](https://eng.libretexts.org/Courses/California_State_Polytechnic_University_Humboldt/Mechanical_Behavior_of_Material/Chapter_8%3A_Beam_Bending%2C_Buckling%2C_and_Torsion) (Chapter 8: Beam Bending, Buckling, and Torsion; inspected passage indices 191, 197, 199, 201, 215, 216, 217 (zero-based in saved snapshot); HTML anchors: paragraph-192; paragraph-198; paragraph-200; paragraph-202; paragraph-216; paragraph-217; paragraph-218), [e39](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_of_Materials_(Roylance)/04%3A_Bending/4.02%3A_Stresses_in_Beams) (4.2: Stresses in Beams; inspected passage indices 68, 72 (zero-based in saved snapshot); HTML anchors: section_1; section_2)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Chandra X-ray Observatory · local:catalog:chandra-x-ray-observatory
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Four paired grazing-angle mirrors, smoothness, iridium coating and precision alignment are supported by Chandra. The newly added NASA source supplies the cosmic imaging context. Its unrelated overbroad Great Observatories wording is not adopted.
Sources: [b03](https://chandra.harvard.edu/about/telescope_system.html) (Chandra :: About Chandra :: Telescope System
      ; inspected passage indices 10, 11, 12, 13, 14, 16 (zero-based in saved snapshot); HTML anchors: content), [p25](https://science.nasa.gov/mission/chandra/) (Chandra X-ray Observatory; inspected passage indices 5, 22 (zero-based in saved snapshot); HTML anchors: paragraph-6; paragraph-23)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Chemical bond · Q44424
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The bonding chapter supports the general definition; ionic-bond passages support the mobility/conductivity example. The card treats ionic behavior as an example rather than all bonding.
Sources: [c02](https://openstax.org/books/chemistry-2e/pages/7-1-ionic-bonding) (7.1 Ionic Bonding; inspected passage indices 6, 12 (zero-based in saved snapshot); HTML anchors: fs-idm91147568; fs-idm8803008), [c20](https://openstax.org/books/chemistry-2e/pages/7-introduction) (Ch. 7 Introduction; inspected passage indices 8 (zero-based in saved snapshot); HTML anchors: fs-idp26683312)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Graph theory · local:authored:000604
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: finding.
The card and adjacency-matrix relationship are supported. The learning takeaway adds bipartite colorability, which is absent from both attached passages.
Sources: [m18](https://mathworld.wolfram.com/GraphTheory.html) (Graph Theory -- from Wolfram MathWorld; inspected passage indices 1 (zero-based in saved snapshot); HTML anchors: paragraph-2), [m21](https://mathworld.wolfram.com/AdjacencyMatrix.html) (Adjacency Matrix -- from Wolfram MathWorld; inspected passage indices 1, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Oscillator quality factor · local:catalog:oscillator-quality-factor
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The damping/linewidth relation and tuned-radio example are explicit in p09; added p08 supplies persistence/decay evidence. Both references support the corrected resonance relationship bundle. No disputed numeric Q formula is repeated.
Sources: [p09](https://openstax.org/books/university-physics-volume-1/pages/15-6-forced-oscillations) (15.6 Forced Oscillations; inspected passage indices 16 (zero-based in saved snapshot); HTML anchors: fs-id1167131421041), [p08](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations) (15.5 Damped Oscillations; inspected passage indices 9 (zero-based in saved snapshot); HTML anchors: fs-id1167131181569)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Euler’s polyhedron formula · local:catalog:eulers-polyhedron-formula
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The displayed V-E+F=2 and genus-zero special case support the card. Sphere-like topology retains the necessary limitation; handle-bearing surfaces are explicitly distinguished.
Sources: [m26](https://mathworld.wolfram.com/PolyhedralFormula.html) (Polyhedral Formula -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4), [m02](https://mathworld.wolfram.com/EulerCharacteristic.html) (Euler Characteristic -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Orientable surface · local:catalog:orientable-surface
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The continuous tangent-plane structure and one-sided Möbius example support the ordinary orientation explanation. The contrast is labeled editorial rather than pretending the abstract definition asserts this learning bridge.
Sources: [m05](https://mathworld.wolfram.com/OrientableSurface.html) (Orientable Surface -- from Wolfram MathWorld; inspected passage indices 1 (zero-based in saved snapshot); HTML anchors: paragraph-2), [m03](https://mathworld.wolfram.com/MoebiusStrip.html) (Möbius Strip -- from Wolfram MathWorld; inspected passage indices 1 (zero-based in saved snapshot); HTML anchors: paragraph-2)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Unit cell · local:catalog:unit-cell
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
IUCr distinguishes primitive from multiple cells and OpenStax explains boundary sharing. Lattice points are not conflated with numbers of atoms in an arbitrary basis.
Sources: [b01](https://dictionary.iucr.org/Unit_cell) (Unit cell; inspected passage indices 8, 9 (zero-based in saved snapshot); HTML anchors: paragraph-9; paragraph-10), [c11](https://openstax.org/books/chemistry-2e/pages/10-6-lattice-structures-in-crystalline-solids) (10.6 Lattice Structures in Crystalline Solids; inspected passage indices 10, 13 (zero-based in saved snapshot); HTML anchors: fs-idm2181616; fs-idm15054992)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Homeomorphism · local:catalog:homeomorphism
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
Continuity of the bijection and inverse, and the isometry contrast, are explicit. Graph-subdivision evidence corroborates the separate graph sense; the card itself consistently describes topological-space equivalence.
Sources: [m16](https://mathworld.wolfram.com/Homeomorphism.html) (Homeomorphism -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3), [m58](https://mathworld.wolfram.com/GraphSubdivision.html) (Graph Subdivision -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Matrix-tree theorem · local:catalog:matrix-tree-theorem
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The added finite qualifier and retained simple/unweighted/undirected conditions agree with the Laplacian definition. A principal cofactor has positive cofactor sign, so deleting the same row and column yields the stated tree count.
Sources: [m23](https://mathworld.wolfram.com/MatrixTreeTheorem.html) (Matrix Tree Theorem -- from Wolfram MathWorld; inspected passage indices 1 (zero-based in saved snapshot); HTML anchors: paragraph-2), [m22](https://mathworld.wolfram.com/LaplacianMatrix.html) (Laplacian Matrix -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### NuSTAR · local:catalog:nustar
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
High-energy X-ray targets and black-hole spin result appear in the official mission description. The correction softens direct measurement to observational estimation and avoids implying that radiation escapes from inside a black hole.
Sources: [p31](https://science.nasa.gov/mission/nustar/) (NuSTAR; inspected passage indices 5 (zero-based in saved snapshot); HTML anchors: paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Transiting Exoplanet Survey Satellite · local:catalog:transiting-exoplanet-survey-satellite
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The retained historical design wording avoids presenting the prelaunch plan as an uncompleted future promise. The change from later measurements to follow-up studies better bounds the prospective characterization claims. Bright-star follow-up and transit application are explicit.
Sources: [p28](https://www.nasa.gov/reference/the-transiting-exoplanet-survey-satellite/) (The Transiting Exoplanet Survey Satellite; inspected passage indices 7, 10, 11, 15 (zero-based in saved snapshot); HTML anchors: paragraph-8; paragraph-11; paragraph-12; paragraph-16)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Fatigue (material) · Q507234
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The metal-specific local-flaw mechanism and sometimes-below-yield qualification match Roylance. The source explicitly introduces S-N diagrams as fatigue-life measurements.
Sources: [e38](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_of_Materials_(Roylance)/06%3A_Yield_and_Fracture/6.05%3A_Fatigue) (6.5: Fatigue; inspected passage indices 68, 69 (zero-based in saved snapshot); HTML anchors: section_1)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Mario J. Molina · local:catalog:mario-j-molina
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The named chemist and Rowland attribution, CFC connection, chlorine release and catalytic regeneration are supported. The card omits unrelated medical and quantitative claims.
Sources: [c09](https://openstax.org/books/chemistry-2e/pages/12-7-catalysis) (12.7 Catalysis; inspected passage indices 24, 25, 27 (zero-based in saved snapshot); HTML anchors: fs-idm242073328; fs-idm4297296; fs-idm225343040)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Eiffel Tower · local:catalog:eiffel-tower
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
The official monument source supports the temporary twenty-year plan, radio/science role and preservation. Repurposing is a reasonable stated illustration, not a fabricated quantitative cause claim.
Sources: [e47](https://www.toureiffel.paris/en/the-monument/key-figures) (Eiffel Tower information : facts, height in feet, weight, ...; inspected passage indices 3, 7, 8 (zero-based in saved snapshot); HTML anchors: paragraph-4; paragraph-8; paragraph-9)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Atacama Large Millimeter Array · Q725364
Group: risk_selected. Scope: full_fixed_sample_claim_identity_relationship_audit. Result: supported.
ESO supports cold-cloud observations, high/dry site, atmospheric water absorption and variable-baseline resolution. The application-of-interferometry relationship is directly asserted.
Sources: [p34](https://www.eso.org/public/teles-instr/alma/) (ALMA; inspected passage indices 3, 5, 7, 14 (zero-based in saved snapshot); HTML anchors: paragraph-4; paragraph-6; paragraph-8; paragraph-15)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Conservation of energy · Q11382
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The mechanical-system qualifier and added thermal-damping evidence support energy accounting across forms/boundaries. The text distinguishes mechanical loss from total-energy destruction; its example relationship is editorial.
Sources: [p02](https://openstax.org/books/university-physics-volume-1/pages/8-3-conservation-of-energy) (8.3 Conservation of Energy; inspected passage indices 6, 10, 11, 13 (zero-based in saved snapshot); HTML anchors: fs-id1165036730634; fs-id1165037156176; fs-id1165037052216; fs-id1165036788158), [p08](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations) (15.5 Damped Oscillations; inspected passage indices 9 (zero-based in saved snapshot); HTML anchors: fs-id1167131181569)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Heat engine · Q178185
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Cyclic-engine wording appropriately bounds hot-source/work/cold-sink accounting. Steam-generation example and the two-reservoir Carnot limit are explicit in the sources.
Sources: [e31](https://openstax.org/books/university-physics-volume-2/pages/4-2-heat-engines) (4.2 Heat Engines; inspected passage indices 6, 8, 9 (zero-based in saved snapshot); HTML anchors: fs-id1167586268105; fs-id1167585966477; fs-id1167586179099)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### James Webb Space Telescope · Q186447
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Five-layer shielding and solar orbit near Sun-Earth L2 are supported. Near L2 avoids treating the observatory as stationary at the exact equilibrium point.
Sources: [p33](https://science.nasa.gov/mission/webb/) (James Webb Space Telescope; inspected passage indices 2, 15, 75 (zero-based in saved snapshot); HTML anchors: paragraph-3; paragraph-16; paragraph-76)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Herschel Space Observatory · Q209630
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The corrected statement assigns near-absolute-zero cooling to instrument detectors, as ESA does, rather than all telescope components. Wavelengths, forming systems and water tracing are supported; Spitzer comparison is editorial.
Sources: [p35](https://www.esa.int/Science_Exploration/Space_Science/Herschel_overview) (ESA; inspected passage indices 8, 9, 10, 13, 14, 16 (zero-based in saved snapshot); HTML anchors: paragraph-9; paragraph-10; paragraph-11; paragraph-14; paragraph-15; paragraph-17)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Control engineering · Q4917288
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The revised feedback example avoids defining all control engineering as feedback. The PID reference supplies measured/target error, motor-speed use, accumulated offset and overshoot premises.
Sources: [e26](https://www.mathworks.com/discovery/pid-control.html) (What Is PID Control?; inspected passage indices 68, 70, 72, 74, 76 (zero-based in saved snapshot); HTML anchors: paragraph-69; paragraph-71; paragraph-73; paragraph-75; paragraph-77)
Relationships: 0 checked; see exact target/type/assertion records in audit.initial.json.

### Buoyancy · Q6497624
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Static-fluid and initial-release qualifications bound the buoyancy/acceleration explanation. The source supports displaced-fluid weight and buoyancy on sinking objects. The canal analogy has explicit floating/lifting water premises.
Sources: [p11](https://openstax.org/books/university-physics-volume-1/pages/14-4-archimedes-principle-and-buoyancy) (14.4 Archimedes’ Principle and Buoyancy; inspected passage indices 7, 11, 13, 17 (zero-based in saved snapshot); HTML anchors: fs-id1170958667771; fs-id1170958881037; fs-id1170958653811; fs-id1170958638580)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Photoelectric effect · Q83213
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Single-photon, fixed-frequency conditions bound the photoemission statement. Added Einstein passages, stopping-potential equation and intensity comparison support the correction; matter-wave comparison stays editorial.
Sources: [p18](https://openstax.org/books/university-physics-volume-3/pages/6-2-photoelectric-effect) (6.2 Photoelectric Effect; inspected passage indices 6, 14, 15, 20, 21, 22, 23, 25 (zero-based in saved snapshot); HTML anchors: fs-id1163709773708; fs-id1163713174554; fs-id1163713274860; fs-id1163713428401; fs-id1163709678905; fs-id1163713527138; fs-id1163713118837; fs-id1163713536791)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Second moment of area · Q835065
Group: additional_targeted. Scope: reference_metadata_change_check_with_unchanged_claim_relation_diff. Result: supported.
Reference-metadata-only targeted check: revised e42 locator includes its EI bending formula. Text and relationship are unchanged from revision 1; this does not constitute a new full factual audit of the extra targeted card.
Sources: [e40](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_Map_(Moore_et_al.)/17%3A_Appendix_2_-_Moment_Integrals/17.5%3A_Area_Moments_of_Inertia_via_Integration) (17.5: Area Moments of Inertia via Integration; inspected passage indices 67, 71, 72 (zero-based in saved snapshot); HTML anchors: paragraph-68; section_1), [e42](https://eng.libretexts.org/Courses/California_State_Polytechnic_University_Humboldt/Mechanical_Behavior_of_Material/Chapter_8%3A_Beam_Bending%2C_Buckling%2C_and_Torsion) (Chapter 8: Beam Bending, Buckling, and Torsion; inspected passage indices 217 (zero-based in saved snapshot); HTML anchors: paragraph-218)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Euler characteristic · Q852973
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The finite-triangulation qualification supports V-E+F without asserting a count for arbitrary decompositions. Source table gives sphere 2 and torus 0; genus linkage is explicit.
Sources: [m02](https://mathworld.wolfram.com/EulerCharacteristic.html) (Euler Characteristic -- from Wolfram MathWorld; inspected passage indices 1, 2, 4, 6, 7 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-5; paragraph-7; paragraph-8)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Crystal structure · Q895901
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new periodic qualifier agrees with IUCr crystal-pattern assumptions and avoids implying that this periodic construction covers every broader notion of crystalline order.
Sources: [b02](https://dictionary.iucr.org/Crystal_pattern) (Crystal pattern; inspected passage indices 8, 9, 10, 11 (zero-based in saved snapshot); HTML anchors: paragraph-9; paragraph-10; paragraph-11; paragraph-12), [c11](https://openstax.org/books/chemistry-2e/pages/10-6-lattice-structures-in-crystalline-solids) (10.6 Lattice Structures in Crystalline Solids; inspected passage indices 10 (zero-based in saved snapshot); HTML anchors: fs-idm2181616)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Topology · local:authored:000605
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new reversible qualifier avoids equating arbitrary continuous maps with topology-preserving equivalence. Circle/ellipse and connectivity examples agree with the source.
Sources: [m01](https://mathworld.wolfram.com/Topology.html) (Topology -- from Wolfram MathWorld; inspected passage indices 1, 4, 6, 7 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-5; paragraph-7; paragraph-8)
Relationships: 0 checked; see exact target/type/assertion records in audit.initial.json.

### Activation energy · local:catalog:activation-energy
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The collision-model qualification is appropriate; insufficient collision energy and transition-state barrier agree with the passage and diagram. The Arrhenius connection is explicit later in the same section.
Sources: [c08](https://openstax.org/books/chemistry-2e/pages/12-5-collision-theory) (12.5 Collision Theory; inspected passage indices 18, 21, 23 (zero-based in saved snapshot); HTML anchors: fs-idm58992896; fs-idm102149680; fs-idm92123120)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Angular momentum · local:catalog:angular-momentum
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Classical particle/origin qualifications match r cross p. Straight-line angular momentum and origin dependence are explicit, and the gyroscope source supports torque-induced direction change.
Sources: [p03](https://openstax.org/books/university-physics-volume-1/pages/11-2-angular-momentum) (11.2 Angular Momentum; inspected passage indices 9, 11, 13, 17 (zero-based in saved snapshot); HTML anchors: fs-id1165038184327; fs-id1165038218862; fs-id1165038332421; fs-id1165038202948)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Body-centered cubic structure · local:catalog:body-centered-cubic-structure
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new monatomic bound preserves the two-atoms/eight-neighbors result for the modeled BCC structure, rather than arbitrary atom bases on a BCC lattice.
Sources: [c11](https://openstax.org/books/chemistry-2e/pages/10-6-lattice-structures-in-crystalline-solids) (10.6 Lattice Structures in Crystalline Solids; inspected passage indices 29, 30 (zero-based in saved snapshot); HTML anchors: fs-idp78313376; fs-idm23808480)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Buffer capacity · local:catalog:buffer-capacity
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The revised approximate pH claim and shared-locator correction are supported by the equal-ratio, different-concentration example. It does not promise concentration-independent exact pH.
Sources: [c14](https://openstax.org/books/chemistry-2e/pages/14-6-buffers) (14.6 Buffers; inspected passage indices 38 (zero-based in saved snapshot); HTML anchors: fs-idm103629216)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Buffer solution · local:catalog:buffer-solution
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The added capacity passage supports finite resistance. The unchanged text, acid/base conversion mechanism and relationship now have adequate coverage.
Sources: [c14](https://openstax.org/books/chemistry-2e/pages/14-6-buffers) (14.6 Buffers; inspected passage indices 7, 8, 38 (zero-based in saved snapshot); HTML anchors: fs-idm127493136; fs-idp41915456; fs-idm103629216)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Bumpless transfer · local:catalog:bumpless-transfer
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
One-implementation wording and revised related-to relation correctly avoid treating PID as necessary to every bumpless-transfer design. Internal tracking and pre-switch output alignment are explicit.
Sources: [e35](https://www.mathworks.com/help/simulink/slref/bumpless-control-transfer-between-manual-and-pid-control.html) (Bumpless Control Transfer Between Manual and PID Control; inspected passage indices 1, 11, 15, 16, 17, 19 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-12; paragraph-16; paragraph-17; paragraph-18; paragraph-20)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Cascade control · local:catalog:cascade-control
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new helps-reject wording avoids guaranteeing perfect disturbance removal. The source states outer setpoint control and faster inner response; its engineering bridge remains editorial.
Sources: [e36](https://www.mathworks.com/help/control/ug/designing-cascade-control-system-with-pi-controllers.html) (Designing Cascade Control System with PI Controllers; inspected passage indices 3, 4, 5 (zero-based in saved snapshot); HTML anchors: paragraph-4; paragraph-5; paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Catalan numbers · local:catalog:catalan-numbers
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Fixed vertices/noncrossing diagonals preserve the source convention that orientations count separately. Tree enumeration and the editorial surface-triangulation bridge are adequately distinguished.
Sources: [m29](https://mathworld.wolfram.com/CatalanNumber.html) (Catalan Number -- from Wolfram MathWorld; inspected passage indices 1, 4, 5 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-5; paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Combining equilibrium constants · local:catalog:combining-equilibrium-constants
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Reciprocal, power and product rules are explicit. The added common-temperature bound is consistent with the temperature-specific equilibrium constant; no unsupported arithmetic generalization remains.
Sources: [c04](https://openstax.org/books/chemistry-2e/pages/13-2-equilibrium-constants) (13.2 Equilibrium Constants; inspected passage indices 97, 98, 99, 100 (zero-based in saved snapshot); HTML anchors: fs-idm374944688; fs-idm328298096; fs-idm336251504; fs-idm351795744)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Conditional expectation · local:catalog:conditional-expectation
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Integrability is now explicit. The measurable-random-variable definition and eventwise integral equality support retaining information and preserving conditional averages.
Sources: [m41](https://mathworld.wolfram.com/ConditionalExpectation.html) (Conditional Expectation -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Covalent network solid · local:catalog:covalent-network-solid
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The changed often qualifier avoids treating all network solids as uniformly hard. Network disruption and diamond example are supported; graphite exceptions are not contradicted.
Sources: [c10](https://openstax.org/books/chemistry-2e/pages/10-5-the-solid-state-of-matter) (10.5 The Solid State of Matter; inspected passage indices 14 (zero-based in saved snapshot); HTML anchors: fs-idm59353248)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Electroplating · local:catalog:electroplating
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Silver anode behavior is now explicitly an example. Cathodic reduction and current/voltage/composition effects agree with the described setup.
Sources: [c16](https://openstax.org/books/chemistry-2e/pages/17-7-electrolysis) (17.7 Electrolysis; inspected passage indices 21, 22, 23, 24 (zero-based in saved snapshot); HTML anchors: fs-idm182126896; fs-idm52313424; fs-idm104543584; fs-idm28358112)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Euler column buckling · local:catalog:euler-column-buckling
Group: additional_targeted. Scope: reference_metadata_change_check_with_unchanged_claim_relation_diff. Result: supported.
Reference-metadata-only targeted check: the revised shared e42 locator retains the pinned-column derivation. Claim/relationship diff is unchanged; no new full factual audit is claimed for this extra targeted card.
Sources: [e42](https://eng.libretexts.org/Courses/California_State_Polytechnic_University_Humboldt/Mechanical_Behavior_of_Material/Chapter_8%3A_Beam_Bending%2C_Buckling%2C_and_Torsion) (Chapter 8: Beam Bending, Buckling, and Torsion; inspected passage indices 225, 230, 231, 236, 237, 238, 239, 240, 241, 242 (zero-based in saved snapshot); HTML anchors: paragraph-226; paragraph-231; paragraph-232; paragraph-237; paragraph-238; paragraph-239; paragraph-240; paragraph-241; paragraph-242; paragraph-243)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Face-centered cubic structure · local:catalog:face-centered-cubic-structure
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The added monatomic qualifier correctly bounds the four-atom conventional-cell count and twelve-neighbor result. The CCP/ABC comparison is explicit in the next paragraph.
Sources: [c11](https://openstax.org/books/chemistry-2e/pages/10-6-lattice-structures-in-crystalline-solids) (10.6 Lattice Structures in Crystalline Solids; inspected passage indices 31, 32 (zero-based in saved snapshot); HTML anchors: fs-idp30613264; fs-idp4268832)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Fail-safe track-circuit signalling · local:catalog:fail-safe-track-circuit-signalling
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Explicit Network Rail attribution and normally wording match the operator’s qualified failure behavior. The text does not promise every conceivable failure is safe.
Sources: [e45](https://www.networkrail.co.uk/stories/track-circuits-explained/) (Track circuits explained; inspected passage indices 8, 9, 10, 12 (zero-based in saved snapshot); HTML anchors: paragraph-9; paragraph-10; paragraph-11; paragraph-13)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### First-order reaction half-life · local:catalog:first-order-reaction-half-life
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Fixed conditions correctly bound the constant-rate-constant exponential loss. Equal fractional rather than equal absolute losses and independence from starting concentration are supported.
Sources: [c07](https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws) (12.4 Integrated Rate Laws; inspected passage indices 70, 72, 74, 75 (zero-based in saved snapshot); HTML anchors: fs-idm99562880; fs-idp162624; fs-idp123084256; fs-idm124479504)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Gauss–Bonnet theorem · local:catalog:gaussbonnet-theorem
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Compact, smooth, two-dimensional and boundaryless assumptions match the theorem. The source explicitly relates the curvature integral to Euler characteristic and explains redistribution under deformation.
Sources: [m09](https://mathworld.wolfram.com/Gauss-BonnetFormula.html) (Gauss-Bonnet Formula -- from Wolfram MathWorld; inspected passage indices 4, 5 (zero-based in saved snapshot); HTML anchors: paragraph-5; paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Gaussian curvature · local:catalog:gaussian-curvature
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The product formula was inspected, including image alt text. The nonzero matching-sign correction avoids incorrectly classifying a zero principal curvature as positive curvature.
Sources: [m08](https://mathworld.wolfram.com/GaussianCurvature.html) (Gaussian Curvature -- from Wolfram MathWorld; inspected passage indices 1, 13, 21, 23 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-14; paragraph-22; paragraph-24)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Geometric distribution · local:catalog:geometric-distribution
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Fixed positive success probability and independent trials are supported. Trial/failure conventions are separated; no learning-dependent probability is silently included.
Sources: [b05](https://openstax.org/books/introductory-statistics-2e/pages/4-4-geometric-distribution) (4.4 Geometric Distribution; inspected passage indices 2, 4, 5, 7, 8 (zero-based in saved snapshot); HTML anchors: list-00001; list-00002), [m40](https://mathworld.wolfram.com/GeometricDistribution.html) (Geometric Distribution -- from Wolfram MathWorld; inspected passage indices 3, 4 (zero-based in saved snapshot); HTML anchors: paragraph-4; paragraph-5)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Golden Gate Bridge · local:catalog:golden-gate-bridge
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The historic longest-span claim, 4,200 feet and critics’ site concerns are supported. Attribution to critics correctly avoids presenting their feasibility judgment as objective fact.
Sources: [e12](https://www.asce.org/about-civil-engineering/history-and-heritage/historic-landmarks/golden-gate-bridge) (Golden Gate Bridge | ASCE
; inspected passage indices 4, 6, 7 (zero-based in saved snapshot); HTML anchors: paragraph-5; paragraph-7; paragraph-8)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Henderson–Hasselbalch equation · local:catalog:hendersonhasselbalch-equation
Group: additional_targeted. Scope: reference_metadata_change_check_with_unchanged_claim_relation_diff. Result: supported.
Reference-metadata-only check: c14 now includes the needed buffer passages. Card and relationship are byte-equivalent to revision 1 apart from version; no new full factual audit is claimed for this extra targeted card.
Sources: [c14](https://openstax.org/books/chemistry-2e/pages/14-6-buffers) (14.6 Buffers; inspected passage indices 49, 50, 51 (zero-based in saved snapshot); HTML anchors: fs-idp10558896; fs-idp7990848; fs-idp97287200)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Hexagonal close packing · local:catalog:hexagonal-close-packing
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The ideal-packing qualification is appropriate. ABAB versus ABC and coordination twelve match the inspected close-packing discussion.
Sources: [c11](https://openstax.org/books/chemistry-2e/pages/10-6-lattice-structures-in-crystalline-solids) (10.6 Lattice Structures in Crystalline Solids; inspected passage indices 33 (zero-based in saved snapshot); HTML anchors: fs-idp178963488)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Ideal rocket equation · local:catalog:ideal-rocket-equation
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Constant effective exhaust speed and neglected gravity/drag bound the ideal relation. At fixed dry mass the diminishing marginal gain follows the logarithm; the specific-impulse form is explicit.
Sources: [e21](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/) (Ideal Rocket Equation | Glenn Research Center | NASA; inspected passage indices 2, 13, 21, 28, 31, 35, 36, 39, 40, 41, 43 (zero-based in saved snapshot); HTML anchors: paragraph-3; paragraph-14; paragraph-22; paragraph-29; paragraph-32; paragraph-36; paragraph-37; paragraph-40; paragraph-41; paragraph-42; paragraph-44)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Le Châtelier’s principle · local:catalog:le-chateliers-principle
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new fixed-temperature condition bounds the volume comparison. Differing gas stoichiometry and temperature-dependent direction match the examples.
Sources: [c05](https://openstax.org/books/chemistry-2e/pages/13-3-shifting-equilibria-le-chateliers-principle) (13.3 Shifting Equilibria: Le Châtelier’s Principle; inspected passage indices 5, 24, 42 (zero-based in saved snapshot); HTML anchors: fs-idp113339808; fs-idm173238784; fs-idp156642144)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Markov’s inequality · local:catalog:markovs-inequality
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The finite-mean qualification, nonnegative random variable and positive threshold are appropriate; the displayed inequality supports the bound. The Chebyshev derivation explicitly invokes Markov.
Sources: [m44](https://mathworld.wolfram.com/MarkovsInequality.html) (Markov's Inequality -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Martingale · local:catalog:martingale
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Finite means and conditioning on the entire past are explicit in the definition. Symmetric random-walk example supports the zero-expected-change illustration.
Sources: [m42](https://mathworld.wolfram.com/Martingale.html) (Martingale -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Method of initial rates · local:catalog:method-of-initial-rates
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The new otherwise-matched-conditions qualification fits the experimental comparison. Holding one concentration constant and ratio-based order inference are explicit.
Sources: [c06](https://openstax.org/books/chemistry-2e/pages/12-3-rate-laws) (12.3 Rate Laws; inspected passage indices 29, 37, 39 (zero-based in saved snapshot); HTML anchors: fs-idm147402384; fs-idp221247360; fs-idm59663552)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Miter lock gate · local:catalog:miter-lock-gate
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The Panama-original-design qualifier bounds hollow buoyant gate construction. V closing, reduced hinge load and resistance to water pressure are explicit.
Sources: [e43](https://pancanal.com/en/design-of-the-locks/) (Design Of The Locks; inspected passage indices 18, 19 (zero-based in saved snapshot); HTML anchors: paragraph-19; paragraph-20)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### PID control · local:catalog:pid-control
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Basic-formulation qualification leaves room for practical derivative variants. Present, accumulated and rate-of-change error terms are supported; anti-windup source explicitly treats saturation in PID.
Sources: [e26](https://www.mathworks.com/discovery/pid-control.html) (What Is PID Control?; inspected passage indices 68, 70, 72, 74 (zero-based in saved snapshot); HTML anchors: paragraph-69; paragraph-71; paragraph-73; paragraph-75)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Pressure thrust · local:catalog:pressure-thrust
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Uniform exit-pressure qualification supports replacing a pressure integral by pressure difference times area. The thrust equation separately retains momentum flow when this term vanishes.
Sources: [e04](https://www.grc.nasa.gov/www/k-12/airplane/specimp.html) (Specific Impulse; inspected passage indices 4 (zero-based in saved snapshot); HTML anchors: paragraph-5)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Quotient group · local:catalog:quotient-group
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Normal-subgroup cosets and induced multiplication are supported. The corrected relationship now restricts the group-order/Lagrange comparison to finite groups while preserving the general quotient construction.
Sources: [m34](https://mathworld.wolfram.com/QuotientGroup.html) (Quotient Group -- from Wolfram MathWorld; inspected passage indices 1, 2, 3 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-4)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Ramp metering · local:catalog:ramp-metering
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Metering’s platoon-breaking benefit is now appropriately modal. The attached handbook relationship source e49 independently supports queue-storage and adjacent-street limitations in the revised card.
Sources: [e46](https://ops.fhwa.dot.gov/freewaymgmt/ramp_metering/about.htm) (About Ramp Metering; inspected passage indices 12, 16, 17 (zero-based in saved snapshot); HTML anchors: contenttext)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Ramsey number · local:catalog:ramsey-number
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The newly stated simple undirected setting matches the two-parameter theorem and party analogy; no numerical Ramsey value is asserted.
Sources: [m28](https://mathworld.wolfram.com/RamseyNumber.html) (Ramsey Number -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Rayleigh criterion · local:catalog:rayleigh-criterion
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The criterion is appropriately called conventional and bounded to an ideal large circular aperture. The maximum/minimum rule and wavelength/diameter dependence match the stated diffraction relation.
Sources: [p15](https://openstax.org/books/university-physics-volume-3/pages/4-5-circular-apertures-and-resolution) (4.5 Circular Apertures and Resolution; inspected passage indices 9, 11, 12, 13 (zero-based in saved snapshot); HTML anchors: fs-id1172101945964; fs-id1172099490776; fs-id1172101788340; fs-id1172101918383)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Scanning tunneling microscopy · local:catalog:scanning-tunneling-microscopy
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Conducting tip/sample and voltage bias are explicit in the model. Gap-sensitive tunneling current supports atomic-scale mapping; wording avoids identifying it with an ordinary optical photograph.
Sources: [p21](https://openstax.org/books/university-physics-volume-3/pages/7-6-the-quantum-tunneling-of-particles-through-potential-barriers) (7.6 The Quantum Tunneling of Particles through Potential Barriers; inspected passage indices 65, 66 (zero-based in saved snapshot); HTML anchors: fs-id1170902851400; fs-id1170901616105)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Silicon passivation · local:catalog:silicon-passivation
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The revised hot strong aqueous-base condition matches the dissolution passage. Surface protection and exposed-silicon reaction remain limited to the described chemistry.
Sources: [c17](https://openstax.org/books/chemistry-2e/pages/18-3-structure-and-general-properties-of-the-metalloids) (18.3 Structure and General Properties of the Metalloids; inspected passage indices 26 (zero-based in saved snapshot); HTML anchors: fs-idm38894288)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Spanning tree · local:catalog:spanning-tree
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Finite connected graph qualification correctly bounds the n-1 edge assertion. The source provides multiple examples and explicitly links the count to the matrix-tree theorem.
Sources: [m19](https://mathworld.wolfram.com/SpanningTree.html) (Spanning Tree -- from Wolfram MathWorld; inspected passage indices 1, 2 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Spitzer Space Telescope · local:catalog:spitzer-space-telescope
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The original cryogenic-design qualifier prevents extending helium cooling to the later warm mission. NASA gives about 5 K and suppression of telescope emission; changed Herschel reference still supports the editorial comparison.
Sources: [p26](https://science.nasa.gov/mission/spitzer/) (Spitzer Space Telescope; inspected passage indices 7, 14, 16 (zero-based in saved snapshot); HTML anchors: paragraph-8; paragraph-15; paragraph-17)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Stellar proper motion · local:catalog:stellar-proper-motion
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The angular-drift definition and Gaia combination with distance/radial velocity are direct. Persistent drift distinguishes it from periodic parallax without implying every measured position change is proper motion.
Sources: [p42](https://www.esa.int/Science_Exploration/Space_Science/Gaia/Proper_motion) (ESA; inspected passage indices 1, 2, 5 (zero-based in saved snapshot); HTML anchors: paragraph-2; paragraph-3; paragraph-6)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Stern–Gerlach experiment · local:catalog:sterngerlach-experiment
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Ground-state silver and nonuniform-field qualifications support the two-band/spin interpretation. The card does not generalize the beam behavior to arbitrary atomic states.
Sources: [p23](https://openstax.org/books/university-physics-volume-3/pages/8-3-electron-spin) (8.3 Electron Spin; inspected passage indices 26, 27 (zero-based in saved snapshot); HTML anchors: fs-id1170902163294; fs-id1170903720942)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Tidal locking · local:catalog:tidal-locking
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Roughly the same lunar face preserves the libration qualification. Tidal dissipation and synchronized periods are explicit; the card does not repeat the source’s speculative future-Earth statement.
Sources: [p07](https://openstax.org/books/university-physics-volume-1/pages/13-6-tidal-forces) (13.6 Tidal Forces; inspected passage indices 37 (zero-based in saved snapshot); HTML anchors: fs-id1168325697191)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Total internal reflection · local:catalog:total-internal-reflection
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The ideal nonabsorbing-interface and propagating-ray wording avoids excluding evanescent fields. Index ordering and critical-angle condition are supported by the Snell-law section.
Sources: [p13](https://openstax.org/books/university-physics-volume-3/pages/1-4-total-internal-reflection) (1.4 Total Internal Reflection; inspected passage indices 7, 10, 11 (zero-based in saved snapshot); HTML anchors: fs-id1172100972304; fs-id1172100960831; fs-id1172100536074)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Track circuit · local:catalog:track-circuit
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Basic relay-based wording preserves the operator example without claiming every track circuit uses the same relay implementation. Wider signalling, occupancy detection and fail-safe comparison are supported.
Sources: [e45](https://www.networkrail.co.uk/stories/track-circuits-explained/) (Track circuits explained; inspected passage indices 2, 3, 6 (zero-based in saved snapshot); HTML anchors: paragraph-3; paragraph-4; paragraph-7)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Variable-area exhaust nozzle · local:catalog:variable-area-exhaust-nozzle
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The unchanged engineering tradeoff is directly supported. The revised related-to link treats converging-diverging geometry as the cited afterburner example, rather than every possible variable-area nozzle.
Sources: [e08](https://www.grc.nasa.gov/www/k-12/airplane/nozzle.html) (Nozzles; inspected passage indices 2 (zero-based in saved snapshot); HTML anchors: paragraph-3)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Zero-force truss member · local:catalog:zero-force-truss-member
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
Ideal truss, specific loading and exactly two collinear members bound the rule correctly. The source explicitly mentions bracing and simpler joint analysis.
Sources: [e24](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Introduction_to_Aerospace_Structures_and_Materials_(Alderliesten)/02%3A_Analysis_of_Statically_Determinate_Structures/05%3A_Internal_Forces_in_Plane_Trusses/5.06%3A_Methods_of_Truss_Analysis) (5.6: Methods of Truss Analysis; inspected passage indices 99, 100, 101, 102 (zero-based in saved snapshot); HTML anchors: paragraph-100; paragraph-101; paragraph-102; paragraph-103)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

### Zone refining · local:catalog:zone-refining
Group: additional_targeted. Scope: targeted_independent_boundary_correction_check. Result: supported.
The added melt-solubility qualification bounds which impurities travel with the moving zone. End removal and semiconductor preparation are supported.
Sources: [c17](https://openstax.org/books/chemistry-2e/pages/18-3-structure-and-general-properties-of-the-metalloids) (18.3 Structure and General Properties of the Metalloids; inspected passage indices 24, 25 (zero-based in saved snapshot); HTML anchors: fs-idm43188096; fs-idm29187152)
Relationships: 1 checked; see exact target/type/assertion records in audit.initial.json.

