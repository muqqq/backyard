# Backyard design project

Landscape plan for a private backyard. Everything in this folder is generated
from `plan.py`; treat that script as the single source of truth and never hand-edit the outputs.

## Files

| File | What it is |
|---|---|
| `plan.py` | Source of truth. Dimensions, geometry, labels. Writes every output below. Run `python3 plan.py`. |
| `viewer_template.html` | Template for the 3D viewer. `plan.py` fills `__GEOM__` and `__SHARE__` and writes `backyard_3d.html` (editor) and `index.html` (view-only). |
| `rectify.py` | Warps the DJI overhead photo into plan view (`photo/base_rectified.jpg`, `photo/base_grid.jpg`). Rerun only if lot dimensions change; corner pixels are hardcoded for `DJI_20260907184453_0183_D.JPG`. |
| `seat_ctrl.json` | Optional. Control points for the seat wall saved from the viewer's edit mode. If present, `plan.py` uses it instead of `SEAT_CTRL`. See "Seat wall editing" below. |
| `backyard_plan.svg` | 2D plan, 1 unit = 1 cm, 1:100 sheet. Opens in Figma, Inkscape, Illustrator. |
| `backyard_plan.dxf` | Same plan in metres, one layer per feature (`SEAT_WALL`, `BLACK_EDGE`, `OPENINGS`, `TREES_REMOVE`, ...). LibreCAD, QCAD, AutoCAD, SketchUp Pro. |
| `backyard_plan_preview.png` | Render of the SVG. |
| `backyard_geom.json` | Geometry as JSON. Also what the 3D viewer embeds. |
| `backyard_3d.html` | The 3D viewer with the seat wall editor (three.js r128 from cdnjs). Published as a Claude artifact, see below. |
| `index.html` | Same viewer with the editor and database switched off (`SHARE = true`). Served by GitHub Pages at https://muqqq.github.io/backyard/ with no sign-in, and also published as a view-only Claude artifact. |
| `photo/dji/` | Drone originals. `0183` is the overhead used for rectification. XMP has gimbal pitch and yaw. |
| `photo/iphone/` | 25 ground photos as HEIC, numbered. `photo_mark.jpeg` marks position (number) and facing direction (arrow) of each. #16 was taken on the deck under the roof. |
| `photo/iphone_jpg/` | JPEG copies of the above, 1 and 21 rotated upright. |
| `photo/base_rectified.jpg` | Overhead photo in plan view, 100 px per metre. Ground texture in the viewer. |
| `photo/plan_over_photo.jpg` | Plan drawn over the rectified photo, the alignment check. |
| `sketch_design.jpg`, `sketch_base.jpg` | The owner's original hand sketches. |

## Regenerate everything

```sh
cd <this folder>
python3 plan.py                      # svg, dxf, json, 3d html
# 2D preview png (Chrome headless):
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --force-device-scale-factor=2.3 --window-size=1020,775 \
  --screenshot=backyard_plan_preview.png file://$PWD/backyard_plan.svg
```

Then republish `backyard_3d.html` with the Artifact tool using the URL below so the link stays the same.
`ezdxf` and `pillow` are installed for the default `python3`. The 3D page can be smoke-tested headless with
`--headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --virtual-time-budget=8000`.

## The published 3D viewer

URL: https://claude.ai/code/artifact/5b503d1a-34d9-412a-96c2-48d6f9727ae7

Republish by passing `file_path: backyard_3d.html` and `url: <that URL>` to the Artifact tool.
View-only copy (no db, shareable): https://claude.ai/code/artifact/646cbdb7-150b-4ece-babf-7f32c7ff1499, republish from `index.html` with that `url`.
GitHub Pages serves `index.html` at https://muqqq.github.io/backyard/ after every `git push` (repo is public; photo/ stays out of it). The page declares
the `db` capability (`capabilities: {"db": {}}`), which is why it cannot be shared by public link, only within the
owner's organisation. Omit `capabilities` on a redeploy to keep it; passing `{}` would clear it and break saving.

Viewer features: six camera presets, sun-hour slider (top of plan is true east), toggles for paver pattern,
trees, house, fence, labels, drone photo as ground, 1 m grid, and the seat wall editor.

## Seat wall editing and the database

The curved seat wall is a Catmull-Rom spline through control points. In `plan.py` the default list is
`SEAT_CTRL` (10 points). Two more points are appended automatically so the wall ends tangent to tree E's ring.

In the viewer, "Edit: drag the orange handles" shows one handle per control point in plan view. Dragging rebuilds
the seat wall, paving and lawn live (JS ports of `spline` and `offset` in the template). "Save shape" writes:

```
collection: design    doc_id: seatWall
{ "pts": [[x, y], ...10 pairs, metres, plan coords], "savedAt": ISO time }
```

to the artifact's database. On load the page reads that doc and, if it has the same number of points as
`SEAT_CTRL`, uses it. "Reset" restores the drawn shape but does not delete the doc.

To bring a saved shape into the plan files:

1. `Artifact` tool, `action: read_db`, `url` as above, `db_op: get`, `collection: design`, `doc_id: seatWall`.
2. Write the result to `seat_ctrl.json` as `{"pts": [[x, y], ...]}`.
3. `python3 plan.py`, regenerate the preview, republish the viewer.

If the number of control points in `SEAT_CTRL` ever changes, the saved doc is ignored until re-saved from the
new handle set. Plan coordinates: origin at the north-east corner, x runs south (right on the sheet), y runs west
(down the sheet, toward the house), metres.

## Site facts that are settled (do not re-derive)

- Orientation: top of the plan is true east, right side is south, house is on the west.
- Lot: 22.8 m across the east fence (owner's tape, approx). North side 10.2 m to the house-left wall.
- Along the house from the north fence: 7.8 m wall, 5.8 m deck, 6.5 m house, entrance derived as 2.7 m
  (owner's tape said 3.2; the drone photo reads about 2.6).
- Deck: 5.8 x 5.7 m, 35 cm high with two steps, outer edge 0.53 m proud of the house-left wall. The house roof
  covers the west 2.6 m of it; 3.2 m is open. South side therefore 15.37 m to the house-right wall.
- Existing concrete strip 0.98 m wide along the house-left wall.
- Trees: positions from the rectified drone photo, three of them tape-corrected. A, B, C and the tree the owner
  circled on the drone photo are to be removed (`remove_trees`). E (9.2, 2.0) and F (5.2, 8.0) stay, each with
  a circular seat wall, inner radius 0.5 m.
- Design: seat wall 40 cm wide, 40 to 50 cm high, no planting bed inside it; black paver edging 15 cm wide, flush,
  1.5 m off the east fence and 1.2 m off the south fence, sweeping into the entrance corner. Concrete pad
  6.5 x 1.5 m hard against the east fence. Lawn 5 cm below paving. Gravel strips 1 m on north and south fences.
- A swimming pool under the middle of the paved area was filled in. Compaction of that fill is the main
  construction risk; raise it before paving is ordered.
- The white board in the ground photos is 0.98 m long, use it as a scale reference.
- Paver field about 178 m² net of the two rings at the last count; recompute from `backyard_geom.json`
  (shoelace on `areas.patio` minus the ring circles) after any change.

## Conventions

- Owner is bilingual; labels on the plan are Chinese first, English second.
- Every measured dimension carries its source in a comment in `plan.py`; derived ones are marked with `*` on
  the sheet. Keep that habit.
- Positions read off photos are good to about ±0.3 m. Tape beats photo.
- Keep the 3D viewer's `<title>` as "Backyard Walkthrough" and its favicon as is.
