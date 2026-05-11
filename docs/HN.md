# HN post — Show HN: unity-loop — Claude vibes a Unity WebGL scene across islo.dev sandboxes

## Title (≤80 chars)
Show HN: Claude tournaments a Unity WebGL scene across parallel sandboxes (unity-loop)

## URL
https://zozo123.github.io/unity-loop-page/

## Body (markdown)
unity-loop is a tiny optimization loop: K parallel [islo.dev](https://islo.dev) sandboxes each render a Unity WebGL build wrapped in a different presentation variant (CSS, page chrome, color filter). A Claude vision call scores each screenshot against a target prompt (`synthwave`, `ominous`, `calm`). Winner is promoted to the gh-pages champion, iframed live on the project page. Trajectory: 1.2/5 → 4.8/5 in 6 rounds.

Stack:
- Unity scene: Lightning VFX by @MirzaBeig (~7MB wasm, fixed across rounds)
- Sandboxes: `islo use --source github://...` + `islo share` per variant
- Server in each sandbox: Caddy with `application/wasm` + `Content-Encoding: gzip` (Unity 2020 `.unityweb` are pre-gzipped) + COOP/COEP for cross-origin isolation
- Proposer: Claude Sonnet 4.6 emits CSS-only JSON variants conditioned on score history
- Judge: same model, given a screenshot and the target prompt, returns `{score, reason}`
- Dashboard: single-file `viz/index.html`, no build step

Why this is not a Unity Editor pipeline: rebuilding wasm requires the `unityci/editor` image (~10GB) and a Unity license dance. That's tier 3, sketched in `docs/POST.md`. This POC iterates on the wrapper around a fixed scene. Honest about it.

Why islo.dev: the only differentiator that mattered here was *cheap parallel cold workers*. K=8 × 6 rounds = 48 sandbox-runs is unergonomic on a single laptop (ports, state, cleanup). `islo use foo` + `islo share foo 8080` is a one-liner per variant.

Headers verified end-to-end through the islo gateway:
- `content-type: application/wasm` ✓
- `content-encoding: gzip` ✓
- `cross-origin-opener-policy: same-origin` ✓
- `cross-origin-embedder-policy: require-corp` ✓
- HTTP/2, 7MB wasm body delivered in 2.4s, streaming mode (no 10MB buffered-mode truncation).

Inspired by my [pokeloop](https://github.com/zozo123/pokeloop) (GA over Pokémon-GO policies on islo) and [meta-harness-on-islo](https://github.com/zozo123/meta-harness-on-islo) (0/5 → 5/5 in 4 proposer steps).

Repo: https://github.com/zozo123/unity-loop · Page: https://zozo123.github.io/unity-loop-page/ · 1080×1080 launch reel: https://zozo123.github.io/unity-loop-page/assets/unity-loop.mp4
