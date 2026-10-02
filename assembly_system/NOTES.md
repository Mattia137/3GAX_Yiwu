# Yiwu — Elevation Growth Lab

`Yiwu Elevation Growth Lab.html` is a single self-contained file (0.24 MB). Double-click it to open. There's no server and no build step. The only thing it loads from the web is three.js (r128, cdnjs), the same as the Podium Lab.

It grows figures from the Yiwu atlas and figure-ground on every elevation of the two towers and the plinth, using the differential growth math from `Differential Growth/01_experiments/dg_core.py`. Then it extrudes each elevation through its mass and intersects them into 3D massing. The output is massing only: no facade detail and no floor split.

## Pipeline

1. **Masses** are read from the Podium Lab.
   - **Towers**: its tower blocks, or its default pair of 46 × 46 m towers on the tower control line. *Tower height* is set here (default 180 m; the airport ceiling allows about 188–192 m above grade).
   - **Plinth**: the original podium geometry, taken down by *Floors down* storeys (default 2, at the Podium Lab's 5.5 m + 4.5 m storeys, so 24 m becomes 14.5 m). The podium comes from one of:
     - the Podium Lab state saved in this browser;
     - a `podium.json` from the Podium Lab's *Download 3D* (*Load Podium Lab JSON…*);
     - the podium control line, as a fallback.

   Blocks above the cut drop out, blocks that cross it are trimmed, and voids still cut.
2. **Faces.** Each tower has four elevations, S, E, N and W, taken on its own rotation. The plinth is grown in plan instead, on three plans (see *Plinth: three plans* below). That gives 11 faces.
3. **Density of figures** (this replaces the earlier volume/void gradient). A tunable field D(u, v) runs from 0 to 1 on every face. Its types are vertical, horizontal, linear at an angle, radial, and edges → centre. Each has start and end density, a midpoint, a sharpness and value noise. It does three things:
   - a seed is kept with the probability the density gives at its centre (*Seeds follow density*);
   - figures shrink by up to 60 % where it is dense (*Smaller where dense*), so more of them fit;
   - the differential growth splits edges fastest where it is dense (*Growth follows*).

   It no longer makes any volume or void itself, and there is no threshold. The grey tone on the elevations shows it. Towers and plinth each have their own density field (*Edit · Towers / Plinth*).
4. **Placement** follows the Podium Lab's genome and Builder.
   - Each face has an 80-gene genome: on, figure, u, v, quarter turn, jitter, scale, growth gain, seed draw. The Podium Lab gene has a height gene; here a growth gain takes its place.
   - Seeds are decoded in order. Each one is pulled toward the centre; a figure still too big for the face is cut by it. A seed is rejected if it overlaps an earlier one or would push the face over the cover cap. It is kept only if its draw is under the density at its centre.
   - *Mutate* uses the Podium Lab's NSGA-II mutation operator. *New genome* reseeds the group.
5. **Seeds** come from one of two sources:
   - **Atlas figures**: the footprints of the Urban Fabric Atlas / Podium Lab library, filtered by family: 115 of its 118, since the three running tracks are left out (`EXCLUDE` in the template).
   - **Figure-ground plate**: a window cut from one of the atlas's twelve 800 × 800 m fabric plates. The plate is tiled, figures are clipped to the face, and the genome slides the window.
6. **Differential growth** is a JS port of `LineGrowth.step`. Each step:
   - springs pull every edge toward L0;
   - Laplacian smoothing, plus bi-Laplacian bending;
   - repulsion keeps different figures R apart and folds of one figure R_self apart. Arc-length exclusion stops neighbours along a curve from repelling, and repulsion is averaged over neighbours (mean mode);
   - the step is clamped and the nodes are kept inside the face;
   - splitting: long edges always split. Other edges split at random with p = min(field · gain · rate / Σw, p cap), but only where an edge is longer than room × L0 and is not in contact with another figure.

   The **growth field is the density** (*Growth follows* sets the coupling), so growth is differential across the face.
7. **Overlap massing.** Each face's mask becomes a signed distance field.
   - Front and back combine: union, overlap or front only.
   - The two directions then intersect (SN ∩ EW) or join (SN ∪ EW).
   - The result is clipped by the original geometry (the footprint SDF per height band, and the base and top).
   - It is meshed with surface nets at the voxel size (default 1 m).

   That gives one closed mesh per mass. It is watertight, with no open edges; checked by counting edge uses. A few edges are shared by four triangles, where two pieces touch along a single voxel edge. *Drop pieces that do not reach the ground* removes floating chunks.

## Overlap count rule (default massing)

Figures **never overlap on a face**: seeds that would overlap are rejected, the growth keeps figures R apart, and an agent can't move onto another figure. Every figure is one **piece**, extruded straight through its mass. Overlaps happen only in 3D, where extrusions from different faces intersect. At every point the extrusions covering it are counted, and a rule table (0, 1, 2 … 7+) says mass or void. The default is parity:

| Pieces at the point | Result |
|---|---|
| 1 | mass |
| 2 (one overlap) | void |
| 3 (two overlaps) | mass |
| 4 (three overlaps) | void |

There are presets for *Any*, *Only 1* and *2+*, and each count can be toggled.

**Overlaps outside the walls become mass** (*Overlap massing*, on by default): the figures run past each face's edges by the *Overhang*, so their extrusions also cross outside the original geometry. Where a piece from S/N crosses a piece from E/W there, and the overlap touches the mass at a wall (directly, or through the overlaps above and below it), it is kept as a small piece of mass outside the envelope, at most one overhang deep. Overlaps outside that don't touch the mass are dropped, so nothing floats. Inside the envelope the rule is unchanged. This works with *Straight · square to the face* edges (the box mesher); the voxel path still clips to the envelope.

- The elevations show the same count, face by face.
- The 3D field is ± the distance to the nearest piece boundary, so surface nets place smooth faces.
- *Massing › Extrusion booleans* switches back to the earlier pipeline: each face's mask, combined front/back, then intersected across.
- **Figures are much bigger.** A figure's largest side is a share of √(face width × height), 50 % by default. Anything still overhanging the face after being pulled toward the centre is cut by it.

## Figures per face and invert

- **Figures per face** (1–80; defaults 14 on the towers, 16 on the plinth) is a target, and it is met.
  - Each figure is sized so the count fills the *Cover* share of the face: area per figure = cover × W × H / count, then *Size ×*, the gene's scale and *Smaller where dense*.
  - Every failed placement (an overlap, or over the cover cap) shrinks the next figure by 3 %.
  - The face's genome is tried first, then extra seeded genes until the count is reached.
  - Tested at 5, 14/16 and 30: every face reached its count.
- **Invert towers** (header button, key I, or *Overlap massing*) swaps mass and void on the towers, and **Invert plinth** (key P) on the plinth only: the faces, the 3D massing and the export. It is the rule table negated inside the original geometry, so a normal and an inverted build add up to the whole envelope (422,411 + 621,852 m³ in the test).

## Plinth: three plans

The plinth is simulated on its own, in plan, not from elevations. It has three plans, each grown with its own genome, density and agents like any face. Each storey of the plinth is the overlap of two of them:

| Floor | Plans |
|---|---|
| Basement, one storey below ground (*Basement depth*, default 4.5 m; 0 = none) | 3 + 1 |
| Ground floor (0 to *Ground floor*, 5.5 m) | 1 + 2 |
| Upper floor (everything above the ground floor, to the plinth top) | 2 + 3 |

In each floor the two plans' figures are extruded through it and counted per cell, and the overlap rule decides: one piece is mass, both is void. *Invert plinth* swaps them. The result is clipped by the plinth's geometry for that band.

**The basement is dug out, not built.** Under the plinth's ground-floor footprint the ground is a slab of earth, 4.5 m deep plus a 1 m earth floor. Where plans 3 + 1 give mass, the earth is removed. That leaves pits you can look down into wherever the ground floor above is open. In 3D the earth is drawn in tan, and the site plane is cut open over the footprint so the pits show. The readout reports *basement dug* in m³, and the plinth's own volume (from 0 m up) no longer includes the basement. The OBJ writes the earth as its own group, `EARTH_PLINTH`. Outside the walls, an overlap of the floor's two plans that touches the mass is kept when *Overlaps outside the walls become mass* is on. On the sheet the plans sit under the towers, labelled with the floors they feed. In 3D and the OBJ, plan 1's curves sit at ground level, plan 2's at the top of the ground floor and plan 3's on the roof.

**Painting the density.** Tick *Paint density* (sheet toolbar, or the Density panel of either group), then drag over any face, tower elevation or plinth plan: the brush raises the density there, and Shift-drag lowers it. *Brush size* and *Brush strength* are in the Density panel. While painting is on, every face shows the density tone more strongly. *Density field › None · uniform, paint only* removes the gradient: the density is *Base density* everywhere (plus any noise), so only what you paint varies it. Releasing the mouse re-seeds that plan and regrows it. The painted density adds to the density field (clamped 0–1), so it steers seeding, figure size and growth like the field does. *Clear painted density* removes it. Paint is saved with *Save settings*.
## Core, floor plans and egress

- **Core**: each tower has a solid core in its middle, through its full height (*Towers + plinth › Core in the middle of each tower*, 10 × 10 m by default, *Core width / depth*).
- **Plans view** (header button *Plans*): every floor of every mass as a small plan, top floor first, with its level, floor area, longest egress route and any bridges. Each mass's header sums them up. The plans are cut from the massing *Plan cut height* (1.2 m) above each floor and rasterised at 0.5 m.
  - Towers: the floor grid (*Tower ground floor* + *Tower floor to floor*).
  - Plinth: the basement (its dug-out space), the ground floor and each upper storey.
- **Ways out**: the tower's core. In the plinth, any tower core that reaches into its plan. On every ground floor, any floor on the outside wall also counts.
- **Egress pathway**: each separate part of a floor is traced to its nearest way out through the walkable area (floor + core + bridges). The plan draws the route from the part's farthest point (dot) in blue.
- **Bridges**: a part with no way out is joined to one by the cheapest rectilinear route.
  - Each new cell costs 1,000 (2,000 outside the original geometry), each turn 1, and walking over existing floor or an earlier bridge nothing. Bridges come out as short as possible, then with as few corners as possible.
  - The route is widened to *Egress bridge width* (1.5 m) and becomes a thin floor plate, *Bridge plate* (0.3 m) thick with its top at the floor level, drawn red in 3D. In the basement it's a passage dug out of the earth instead.
  - Slivers under 4 m² are fragments: drawn as floor, never bridged.
  - The OBJ writes the bridges as `BRIDGES_<mass>` and the earth as `EARTH_PLINTH`.
- **Tested** (default settings): 43 + 43 tower floors and 4 plinth floors. Every part of every floor reaches a way out after bridging. Bridges add about 20 m² per tower floor and about 400 m² across the plinth. Plans take about 0.8 s per mass.
## Floor plate, area and egress checks

- **Tower floor plate and height** (*Towers + plinth*): *Floor plate width ×* and *Floor plate depth ×* (0.4–2.5, shown with the resulting size in metres) scale each tower's footprint about its centre, along its own axes. *Tower height* now runs 40–320 m and is flagged ⚠ above the airport ceiling (about 190 m).
- **GFA** (*Area · egress* panel, the 3D readout and the top of the Plans view): the above-ground floor area, floors + bridges, summed from the floor plans, in m² and sq ft, per tower, for the plinth and in total. The basement is listed apart and not counted. It is checked against *GFA target* (default 46,000 m², the Podium Lab's target).
- **Meet GFA target** raises the figure cover of the towers and the plinth by 0.08 at a time, regrowing and rebuilding each time, until the GFA reaches the target. It stops after 8 tries, at the cover cap, or after 3 tries with no gain, and keeps the best cover. Cover isn't a reliable lever under the overlap rule, so if it can't get there it says to use the floor plate or the height. Tested: from 6,903 m² short, one try met the target (208,083 m²).
- **Bridges are wide enough**: each bridge is at least *Egress bridge width* (now 3 m by default, up to 8 m). It's also at least the width its part of the floor needs: occupants = area / *Load factor* (9.3 m², about 100 sq ft per person), width = occupants × *Width per person* (5 mm), never under *Minimum egress width* (1.1 m). Widths round up to the 0.5 m plan grid, so 3 m becomes 3.5 m. Each plan lists its occupants and its bridge widths, and the summary says whether any bridge is too narrow.
- **Travel distance**: floors whose longest egress route is over *Max travel to exit* (37.5 m, the Podium Lab's) are flagged ⚠ in red. At the default settings most floors are over it: one core per tower, and routes that wind around the voids. More cores or exit stairs would be needed to meet it; for now this is a check only.
## Carved voids: soft porosity after Steven Holl (the default massing)

The overlap count rule fractured the floors: 18–48 separate pieces per floor, about 1,000 bridges, egress routes of 150–200 m. The new method, *Massing › Carved voids · soft (after Holl)*, works the other way round:

- **References.** Li-Ze SOHO (Beijing, 2013 competition) is a subtractive tower: one continuous mass with seven carved sky gardens in its upper portions, and porosity through the ground floor. The Tianjin Ecocity Planning Museum is a block pierced by a few soft, rounded voids; its twin, the Ecology Museum, is their cast, the "additive" reverse ("Bau Gua"). The Sliced Porosity Block (Chengdu) uses a few deliberate urban-scale openings, never fragments.
- **Method.** Each mass starts whole, and every grown figure carves a void exactly where it sits.
  - **Selection:** a face's (or plinth plan's) figures are taken largest first: up to *Figures carved per face* (12), at least *Smallest figure* (6 m²), within *Void budget* (35% of the face).
  - **Shape:** each figure's own outline is rounded on its own, with a disc up to *Rounding* (4 m) but never wider than about half the figure's thickness. No figure is lost, and small ones become soft ellipses. Neighbours closer than the rounding then merge into one void, and inner corners soften. *Grow voids* offsets every outline.
  - **Tower voids** (*Tower voids* menu; it affects only the towers, and the plinth has its own controls): *Soft scoops* carve each figure's rounded outline storey by storey, deepest where the outline is widest. This is the method the base settings were made with, so ase_settings.json sets it (	owerMode: scoop). *Sky gardens* is described next.
  - **Towers: sky gardens.** Each softened void region on a tower face becomes a sky garden spanning whole storeys:
    - its bottom and top snap to the nearest floor levels (at least *Sky garden storeys*, 2);
    - a region taller than *Most storeys* (4) becomes stacked gardens with one solid storey between them;
    - its width is the region's extent across the face;
    - its plan, the same on every storey it spans, is a soft scoop: deepest (*Void depth*, 16 m) mid-width, easing out to the facade at its edges (*Softness*), and never nearer the core than *Core margin* (3 m);
    - gardens are kept largest first until *Garden budget* (25% of the face).
  - **Plinth: each plan cuts its own floors**, following the three-plan logic: plan 1 cuts the ground floor and the basement, plan 2 the ground and upper floors (the plinth's full height above ground), plan 3 the upper floors and the basement. The basement is dug under plan 1's and plan 3's voids.
    - **Large forms, not one hole per figure:** each plan's figures are blurred into a density field over *Merge radius* (12 m), so neighbours merge into large soft forms.
    - **Share:** the voids are the densest part of that field, up to *Void share per plan* (15% of the plinth, and at least a third dense). A floor loses at most two plans' share.
    - **Limits:** at most *Voids per plan* (3) are kept, each at least *Smallest void* (300 m²), rounded by *Void rounding* (10 m).
    - **Setback:** voids from plans 2 and 3 stay *Setback from edge* (8 m) inside the plinth; plan 1's ground-floor voids may reach the edge.
    - **Older settings:** files with *Courts* / *Ground passages* load with *Voids per plan* set to the larger of the two.
    - **Tested** with `No_plinth.json`: 6 voids through all three storeys and into the basement, each floor kept about 15,000 m², and the towers are unchanged.
  - Fragments under 4 m² are removed.
- **Geometry.** Each storey is traced (marching squares) from an analytic field: the signed distance to the envelope, the voids and the core. Edges are smooth curves and straight walls, extruded as prisms; storeys without voids merge. *Invert towers / plinth* gives the void bodies, Tianjin's reverse. *Show the void bodies* draws them translucent in 3D, and the OBJ writes them as `VOIDS_<mass>`. The elevation sheet outlines each void, exactly as carved, on the face or plan it comes from.
- **Result (default build, same growth).** Each tower gets 23 sky gardens and keeps about 70,000 m² of floor (about 54,000 m² with the overlap rule). The towers need 0–3 bridges (about 1,000 with the overlap rule), and every tower floor is within 36 m of the core. Each tower takes about 1.4 s to mesh. A first version that swapped figures for a few generic rounded boxes was too subtle and ignored where the figures sat; it was replaced. The overlap rule and the extrusion booleans are still in the *Massing* menu.

## Floor grid, overhang, Tower East seed

- **Snap to floors** (*Overlap massing › Edges*): one face of each figure lands on the floor-to-floor grid. The choices are the bottom edge (default), the top edge, both, every horizontal edge, or off.
  - The snapped edge becomes the figure's whole bottom (or top): steps that reach past the floor line are trimmed back to it.
  - If a figure is too thin to reshape, it is moved whole onto the line.
  - The grid is a ground floor, then typical floors. For the towers that is *Tower ground floor* and *Tower floor to floor* (default 6.0 m + 4.2 m). The plinth uses its Podium Lab storeys (5.5 m + 4.5 m), the same ones that set *Floors down*.
  - *Floors* in the sheet HUD draws the grid on every face.
  - Tested in the browser: every figure's snapped edge sits on a level (399/399, one leftover in bottom mode).
- **Overhang** (per group, default 10 m on the towers and 5 m on the plinth): the growth domain, the seeds and the agents run this far past every edge of the face. The pattern carries over the edges and cuts into the corners of each mass, and the 3D massing still clips to the original geometry. The sheet shows the overhanging parts in light grey outside each frame. The figure count scales with the extended area, count × (W + 2·O)(H + 2·O) / (W·H), and the cover cap is measured over it too. Each figure keeps its size, so the density on the face stays the same. Tested on the towers at 0, 10 and 30 m of overhang: the face stayed about a quarter covered (23.1 %, 27.3 %, 23.9 %) with 14, 22 and 43 figures per face.
- **Tower East seed**: Tower East grows from Tower West's genome seed + 1, with the same face indices. Untick *Tower East uses Tower West's seed + 1* for identical twins.

## Merged geometry, bigger pieces

- **Merged faces.** The box mesher collects every face rectangle by plane and unions the coplanar ones into polygons, holes included: the boundary is traced on the rectangles' breakpoint grid with the filled side on the left. Each polygon is triangulated with THREE.ShapeUtils, and its outline is kept as the drawn edge.
  - There are no band seams or internal box edges, so each mass reads as one continuous volume.
  - Tested: each mass's volume computed from its mesh matches its cell volume exactly (for example 186,765 m³ = 186,765 m³), so every merged face is complete and wound outward. A tower went from about 38k to 16k triangles.
- **One object.** *Merge towers + plinth into one object* (on by default) writes the whole massing as the single OBJ object `MASSING_MERGED`. The towers still pass into the plinth where they overlap: their frames differ (10° and 11.9°), so that is not a boolean union.
- **Bigger pieces.** *Size ×* goes up to 8 (four times the old maximum of 2). A figure is never shrunk below half its set size to make it fit. At large sizes the target count can't always be met: at ×4, the faces held 2–7 figures instead of 14–16. *Overhang* now goes up to 80 m.

## Straight edges

Each grown figure is regularised before it is drawn, counted or exported.

1. Douglas–Peucker simplification at the *Straightness* tolerance (default 1.5 m).
2. With *Edges › Straight · square to the face* (the default), each edge is snapped to horizontal or vertical. Parallel runs are merged, and runs shorter than *Shortest edge* (default 2.5 m) are dropped.

With square edges, the 3D massing is built exactly from boxes, not voxels:

- z bands start at every vertex height;
- in each band, the S/N pieces cut the a axis into intervals, and the E/W pieces cut the b axis;
- each cell counts the extrusions over it, then the rule and the original geometry decide whether it is mass;
- faces are emitted as merged quads with straight edges.

The plinth's control-line ends are slanted, so there the clip steps every metre. *Straight · any angle* keeps the simplified edges at any angle, and *Organic* shows the raw growth; both go back to voxel surface nets.

## Seeds: atlas board B

The default source picks figures at random from the 107 single figures of the Urban Fabric Atlas's board B (110 less the three running tracks), leaving out the board C landmarks. Each face's genome picks the figure, position, turn and scale. *Atlas families · genome* (filtered by family) and *Figure-ground plate* are still available.

## Agents · diffusion

Every seed figure is an agent, using the settle rule of the vertical city lab (`Differential Growth/03_vertical_city_lab`, SHANCHENG).

**Happiness** is a weighted mean of four terms, each 0–1:

- **density**: the density field under it;
- **3D crossing**: how close the share of its extrusion crossed by figures from the other faces of its mass (the opposite face on the same line, the perpendicular faces at the same height) is to the *target*;
- **support**: what lies under its lowest edge, meaning the ground or another figure;
- **neighbours**: other figures within 3 m of its edge.

**Settling** runs every *n* growth steps, until *Settle until* of the steps:

- The unhappiest share of the agents moves, plus a random tenth of the rest.
- Each mover tries four diffusion hops (gaussian, σ = step × (0.25 + T)) and two quarter turns. It also tries a long hop when restless, or after *Leave after* unhappy moves in a row.
- It takes the happiest pose if that is a gain, or otherwise a random one at temperature T. T anneals from *Restlessness* to 0.

The figure moves rigidly while it keeps growing. The rings on the elevations mark each agent, filled by its happiness. In a test run, mean happiness rose from 0.50 with agents off to 0.55 with them on. Figures as wide as the face cannot move sideways, which limits the gain.

## Export

- **Download OBJ** writes:
  - groups `MASS_TOWER_WEST`, `MASS_TOWER_EAST` and `MASS_PLINTH`, one mesh each;
  - `ELEV_<mass>_<side>`, every grown curve as a closed polyline on its face;
  - `SITE_REDLINE`.

  Units are metres, Z up, in Podium Lab model coordinates (E = x + 511000, N = y + 3246000, ±0.00 = 74.00). In Rhino: File › Import, and tick "Import OBJ groups as layers". At default settings the file is about 20 MB.
- **Saved settings** (panel, open by default): type a name and press *Save* (or Enter). The save holds every parameter, every face's genome and the painted density, and it's kept in this browser in a list, newest first. Each entry has *Load*, *Download* (a `.json` named after it, e.g. `Plinth_courtyards_v2.json`) and *×* (delete, after a confirmation). Saving under an existing name asks before replacing it. *Load from file…* reads a downloaded file back and adds it to the list under its name. Saves opened from disk are shared by every copy of the page opened from disk in the same browser; if the browser blocks storage, the panel says so and saves last only until the page is closed. Settings files from before this change still load.
- **PNG** saves the elevation sheet.

## Towers and plinth simulated separately

The massing settings are kept per group (`cfg.MG.T` and `cfg.MG.P`). The *Massing* panel shows the group selected by *Edit · Towers / Edit · Plinth* (its heading says *towers only* or *plinth only*), and each setting affects only that group's mass. Per group:
- the figure edges (edges, straightness, snap to floors, shortest edge);
- the massing method (carved voids, overlap rule or extrusion booleans), the rule table, invert, overlaps outside the walls, voxel and floating pieces;
- the carving: tower voids, sky gardens and scoops for the towers; courts, passages and court storeys for the plinth.

Only *Build massing when growth finishes* and *Merge … into one object (OBJ)* are shared, marked *· both*. Settings saved before the split, including `base_settings.json`, load into both groups (their *Invert* goes to the towers and *Invert plinth* to the plinth).

Tested: switching the plinth to the overlap rule changed only the plinth (172,595 → 105,064 m³; the towers stayed at 268,894 and 259,132 m³). Changing the towers' rounding and invert changed only the towers.

## Plinth: one plan per floor minus one, and mass from the figures

- **Plans and floors.** The basement has a plan of its own (*basement plan*, `PB`), which makes only the basement. The floors above ground have one plan each, and floor k is made from plans k and k+1, cyclically, so every floor has its own pair and the top floor loops back to the first pair. With the base plinth (*Floors down* 0: G, 1, 2, 3, 4 and a basement) that is B1 = basement plan, G = 1+2, 1 = 2+3, 2 = 3+4, 3 = 4+5, 4 = 5+1. Each plan's label lists the floors it makes. Plans 1–n keep their genome numbers, so older genomes and paint stay on the same plans.
- **The plinth's real shape.** Every plinth plan, and the default plan, takes the plinth's footprint at ground (its blocks, less its voids) instead of a rectangle.
  - **Containment:** seeds that don't fit inside are retried smaller, and growth nodes that push outside are pulled back to the edge (the overhang still lets them run that far past it). Agents only move to spots inside.
  - **Counts:** figure counts and cover use the footprint's area (19,483 m² against the rectangle's 23,735 m² on the base).
  - **Sheet:** the outline is drawn on every plinth plan, and the area outside it is blank.
  - **Tested:** 0 of 14,384 grown points outside.
- **Plinth cores** (*Towers + plinth*: *Plinth cores*, *Plinth core width / depth*; default 0): spread evenly along the plinth's length, each on the deepest point inside its footprint on its line. They are solid through every plinth floor, count as a way out for the floor plans' egress, and are drawn in red on the plinth plans.
- **Figures** (*Plinth massing › Figures · mass from the plans*, the plinth's default in the base settings): each floor's mass is built from its two plans' figures, so it follows them.
  - **Shape:** each figure keeps its own outline, rounded only by *Figure rounding* (2 m, never wider than half its thickness; 0 = exact) and joined to neighbours closer than *Merge neighbours* (3 m).
  - **Each floor:** combines its two plans as *Either plan (union)*, *Both plans (overlap)* or *One plan, not both*.
  - **Coverage:** each floor grows or shrinks evenly to *Coverage*, its share of the footprint (0 = as grown), keeping its shapes.
  - **Pieces:** pieces smaller than *Smallest piece* (40 m²) are dropped, and *Pieces per floor* can keep only the largest few.
  - The basement's dug space is its floor's figures. *Invert plinth* swaps mass and void, as everywhere.
- **Plinth default plan.** On the sheet, *Plinth default plan* sits first in the plinth row. It doesn't grow; it shows the shared paint layer over the plinth's density. With *Paint density* on, paint it alone and the paint reaches every plinth plan. Its first stroke replaces the plans' own paint, so every plan then carries exactly the default paint; a plan can still be painted on its own afterwards, on top of it. When you release, all plans re-seed and regrow. *Same paint on every plinth plan* (Density panel, *Edit · Plinth*) sends strokes made on any plan to the same layer. *Clear painted density* clears it, and it is saved with the settings.
- **Smooth edges** (Figures mode, default 3 m): each plan's figure shapes are blurred over this radius before they are traced. The 2.5 m steps of the square-edged figures become clean curves, and the shapes and their size stay.
- **Tested:**
  - The pairs come out as above, and the towers are unchanged (268,910 / 259,226 m³ on a clean seed).
  - Union, overlap and one-not-both each give a different plinth.
  - Coverage 50% raised the plinth from 120,614 to 137,634 m³.
  - Two dabs on the shared layer raised the density to 1.0 at that point on all three plans.
  - `plinthv1.json` still loads (carved, inverted).

## Base settings

`base_settings.json` (a copy of `Plinthv2.json`, saved 2 Oct 2026; before that `261002_TowerV1.json`) is what the page starts from: every setting, every face's genome and the painted density on the three plinth plans. `build.py` embeds it into the page (which makes the page about 0.6 MB), and the page applies it before the first growth. Settings added after it was saved keep their defaults. *Saved settings › Reset to base settings* goes back to it. To change the base, replace `base_settings.json` (any file saved with *Download*) and rebuild. The base's painted density on the plinth plans was removed (2 Oct), so the plinth starts blank, with the default plan blank too. The base was saved with *Paint density* on, so the page opens with the brush active: dragging on the sheet paints, and right-drag pans.

## Saving and loading

- **What a save holds:** every setting (`cfg`, both groups' massing), every face's genome, all painted density (each face's and the plinth default plan's), the view and its toggles (density tone, curves, floors, 3D face curves and envelope), the group being edited, and any Podium Lab geometry loaded from a file.
- **Loading:** a file is applied over the page's defaults, not over the current settings. A setting the file doesn't have (it didn't exist when the file was saved) takes its default. Tested: with *Plinth cores* at 5 and *Smooth edges* at 9, loading a file without those settings gave 0 and 3, their defaults.

## Rebuilding

Run `python build.py`. It reads `Yiwu Podium Lab.html` (site lines and figure library) and `Yiwu Urban Fabric Atlas.html` (fabric plates), and writes them into `app_template.html` to produce `Yiwu Elevation Growth Lab.html`. Edit the template, then rebuild.

## Caveats

- The Podium Lab's saved state is per browser and per origin. A page opened from disk shares it with the Podium Lab opened from disk in the same browser. Otherwise, use *Load Podium Lab JSON…*.
- Voxel size sets the grain of the massing. 0.5 m is sharper but about 8× the work.
- The 2D growth uses dg_core's linear growth mode with no scale field, and no periodic faces. Each elevation grows on its own, so the curves do not wrap round the corners.
