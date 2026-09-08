# backyard

Landscape plan for our backyard: a measured 2D plan (SVG, DXF) and an interactive 3D walkthrough, all generated from `plan.py`. See `AGENTS.md` for how the files fit together.

## Open the 3D walkthrough

| Link | Sign-in | Seat wall editor | Save |
|---|---|---|---|
| https://muqqq.github.io/backyard/ | none | no | view only |
| https://muqqq.github.io/backyard/backyard_3d.html | none | yes | in that browser only; copy the points from the box to send them on |
| https://claude.ai/code/artifact/5b503d1a-34d9-412a-96c2-48d6f9727ae7 | Claude account | yes | saved to the page's database; Claude can read the shape back into the plan |
| https://claude.ai/code/artifact/646cbdb7-150b-4ece-babf-7f32c7ff1499 | Claude account | no | view only |

The first link is the one to share. It opens in any phone or desktop browser.

## In the viewer

- **Stand here**: overview, on the deck, at the entrance, porch door, kitchen window, lawn corner, plan view.
- **Sun**: time-of-day slider with shadows. Top of the plan is true east.
- **Show**: paver pattern, trees, house, fence, labels, the drone photo as ground, a 1 m grid.
- **Seat wall shape** (editor copies): drag the orange handles in plan view, then Save.
- Drag to orbit, scroll or pinch to zoom, right-drag to pan. "Hide ✕" collapses the panel.

## Files

- `plan.py` generates everything: `backyard_plan.svg`, `backyard_plan.dxf`, `backyard_geom.json`, `backyard_3d.html` (editor) and `index.html` (view only) from `viewer_template.html`.
- `backyard_plan_preview.png` is the rendered plan sheet.
- `sketch_design.jpg`, `sketch_base.jpg` are the original hand sketches.
- Photos are not in this repo.
