# unity-loop — vibe-coding a Unity scene with a Claude-vision tournament on islo.dev

**TL;DR.** I wired the [meta-harness](https://github.com/zozo123/meta-harness-on-islo) proposer/eval loop onto a Unity WebGL build, with islo.dev sandboxes as the parallel worker pool and Claude (vision) as the judge. Given a target prompt like *"synthwave"*, the loop converges from 1.2/5 to 4.8/5 in six rounds. The Unity wasm is fixed; the agent iterates on the presentation wrapper (CSS, page chrome, title, glow). End-to-end demo runs in ~30s with `bin/unity-loop loop --task synthwave`.

## What's actually happening

1. **One Unity scene, K sandboxes per round.** For each round, the proposer emits K JSON variants (CSS, filter, frame color, title). Each variant is rendered by templating `unity/template.html`, dropped into a fresh islo sandbox along with the prebuilt Lightning-VFX wasm, served by Caddy with the right `application/wasm` + `Content-Encoding: gzip` + COOP/COEP headers we [verified end-to-end](https://github.com/zozo123/unity-loop#headers).

2. **Claude judges.** A headless Chromium screenshots each variant's public share URL, the screenshot is sent to Claude Sonnet 4.6 with the task prompt, the model returns `{score, reason}` JSON. K scores per round.

3. **Winner promotes.** Best variant's `(variant, share_url)` is written to `runs/champion.json`, which the gh-pages page reads to update the live iframe.

4. **Proposer reads history.** Next round's variants are conditioned on the best variants and scores so far — a poor man's CMA-ES with an LLM in the search-step.

## What this is *not*

- Not a Unity Editor pipeline. The wasm doesn't change between rounds. Real Unity rebuilds require the `unityci/editor:webgl` image (~10GB), license activation (ULF flow), and a per-iteration build cost in the 30s–2min range. That's a real follow-up: see [Tier 3](#tier-3-real-unity-editor-rebuilds).
- Not RL. There's no policy network. It's a bandit search with an LLM proposer and an LLM judge — closer to evolutionary CSS optimization.

## Why islo.dev for this

The only honest reason to use sandboxes here is **parallel cold workers**. K=8 variants × 6 rounds = 48 sandbox-runs. Doing it locally would block on Caddy ports and machine state. With `islo use ... --source github://...` each variant is a one-line spawn, and `islo share ... 8080` hands back a public URL the judge can hit anonymously.

The other thing that matters: the gateway streams unbuffered. Unity `.wasm.unityweb` files are 7MB gzipped; islo's gateway passes them through with `Content-Encoding: gzip` intact (verified — see headers in the README). If you have a static host that decompresses or re-buffers, Unity dies in the loader.

## Tier 3 — real Unity Editor rebuilds

The natural next step: have Claude write C# scripts in `Assets/`, trigger a headless Unity build inside the sandbox, deploy the new wasm. Sketch:

1. Sandbox image: derive from `unityci/editor:2022.3-webgl-3` (~10GB).
2. License: activate Unity Personal headless via `Unity -batchmode -createManualActivationFile`, upload the .alf to Unity, get a .ulf, ship in the image.
3. Build step: `Unity -batchmode -nographics -projectPath /workspace/proj -buildTarget WebGL -executeMethod BuildScript.Build -quit -logFile -`.
4. Each variant is a real .wasm. Iteration cost ~60s for tiny scenes.

This would turn unity-loop from "CSS-tournament around a fixed game" to "AI-authored Unity gameplay tournament." Worth it. Not in this POC.

## Credits

- Unity scene: [MirzaBeig/Lightning-VFX-WebGL](https://github.com/MirzaBeig/Lightning-VFX-WebGL)
- Sandbox infra: [islo.dev](https://islo.dev)
- Pattern: [pokeloop](https://github.com/zozo123/pokeloop) + [meta-harness-on-islo](https://github.com/zozo123/meta-harness-on-islo)
- Movie: [`agentreel`](https://github.com/islo-labs/agentreel)
