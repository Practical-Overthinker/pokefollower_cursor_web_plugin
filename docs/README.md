# Visuals needed for the main README

The top-level `README.md` has a commented-out visuals block. Capture the files below on a
real Windows machine, drop them in this `docs/` folder with these exact names, then
uncomment the block (and add the screenshots where you want them).

| File | What to capture | Notes |
| --- | --- | --- |
| `demo.gif` | The Pokémon following the cursor across the desktop for ~5–10 s: some fast moves (walk + direction changes), a pause (idle), ideally a brief sleep. | Keep it small — target < 5 MB. ~640–800 px wide, 15–20 fps is plenty. Tools: ScreenToGif, ShareX. |
| `selector.png` | The **Choose Pokémon…** dialog open, with something typed in the search box so the thumbnail grid is filtered. | Default window size is fine. |
| `settings.png` | The **Settings…** dialog. | — |
| `tray.png` | The tray icon with its right-click menu open (Enabled / Choose Pokémon… / Settings… / Exit). | Crop to just the tray area + menu. |

Once `demo.gif` exists, the README's hero image is:

```markdown
![PokéFollower following the cursor](docs/demo.gif)
```

Until then the README ships without images — that's acceptable for the beta, but the demo
GIF is the single highest-value addition for the repo's front page.
