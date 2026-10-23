# unity-loop

**Proof of concept: Claude proposes CSS/page-chrome variants for a fixed Unity WebGL scene, [islo.dev](https://islo.dev/) sandboxes serve them, and Claude vision scores screenshots.**

> **Project page:** https://zozo123.github.io/unity-loop-page/
>
> **Live champion:** expired (islo shares last 24h–7d); the last champion variant is in [`runs/champion.json`](./runs/champion.json).
>
> **Writeup:** [`docs/POST.md`](./docs/POST.md)
>
> **Built on:** [islo.dev](https://islo.dev/) — agent sandboxes with snapshots, shares, gateway egress.
>
> **Inspired by:** [pokeloop](https://github.com/zozo123/pokeloop) (GA over LLM policies), [meta-harness-on-islo](https://github.com/zozo123/meta-harness-on-islo) (proposer/eval loop).

---

## What this is

A bandit-search loop where Claude iterates on the presentation of a Unity WebGL scene. Each variant is a JSON spec of CSS + page chrome wrapped around a fixed Unity build. N islo sandboxes serve N variants in parallel. Claude (vision) judges screenshots against a target prompt. The winner is written to `runs/champion.json`, which the project page reads.

**The Unity wasm is fixed** — Lightning VFX by [@MirzaBeig](https://github.com/MirzaBeig/Lightning-VFX-WebGL). Variation lives in the wrapper. That's the honest thing to do without a 10GB Unity Editor image; rebuilding `.wasm` inside the sandbox is a separate ticket ([`docs/POST.md#tier-3`](./docs/POST.md#tier-3-real-unity-editor-rebuilds)).

## Quick start (offline, deterministic — ~5s)

```bash
bin/unity-loop demo            # 6-round canned trajectory, 1.2 → 4.8 score
bin/unity-loop viz             # serve the dashboard
# open http://localhost:8765
```

You should see the scripted scores **1.2 → 2.4 → 3.1 → 3.7 → 4.4 → 4.8** for task `synthwave`. These are canned values (`DEMO_TRAJECTORY` in `bin/orchestrator.py`), not a measured run: the demo calls neither Claude nor islo. The dashboard shows the same canned trajectory; its preview iframe points at the champion share URL, which has expired.

## Real run (Claude API + N islo sandboxes)

```bash
export ANTHROPIC_API_KEY=...
bin/unity-loop loop --task synthwave --k 4 --steps 6
```

Spawns K islo sandboxes (one per variant), each serving Unity + variant CSS via Caddy, calls Claude vision for the judge round, writes `runs/<run-id>/`, updates `runs/champion.json`. The [project page](https://zozo123.github.io/unity-loop-page/) fetches `runs/champion.json` from this repo's `main` branch on each load.

Run directories are git-ignored, so no real run logs are committed. The committed `runs/champion.json` holds the demo's final variant (score 4.8 from the canned trajectory).

## Layout (mirrors meta-harness-on-islo)

```
islo.yaml             base sandbox config
tasks/<name>/         prompt.md (target aesthetic)
harness/v<N>/         system.md (proposer system prompt)
bin/unity-loop        CLI (demo | loop | eval | propose | host | viz)
bin/orchestrator.py   loop + `demo` (deterministic offline trajectory, DEMO_TRAJECTORY)
bin/proposer.py       reads runs/, asks Claude for next variant
bin/judge.py          Claude-vision scoring of screenshots
bin/host.py           spawns islo sandbox, templates variant, writes the Caddyfile
                      (precompressed gzip + COOP/COEP + application/wasm), shares port 8080
unity/template.html   Unity host with {{TITLE}} {{BG}} {{FILTER}} {{FRAME_COLOR}} {{FRAME_GLOW}} slots
viz/index.html        single-file local dashboard (shows the canned demo trajectory)
runs/                 populated by the loop; runs/champion.json drives the page
```

## Headers

The Unity build ships pre-gzipped `.unityweb` files, so the host has to keep `Content-Encoding: gzip`, serve `application/wasm`, and send COOP/COEP. Checked through the islo share gateway in May 2026 (that share has since expired):

- `content-type: application/wasm`
- `content-encoding: gzip`
- `cross-origin-opener-policy: same-origin`
- `cross-origin-embedder-policy: require-corp`
- HTTP/2; the ~7MB wasm body arrived in 2.4s in that check, streamed (no 10MB buffered-mode truncation)

## Credits

- Unity scene: [MirzaBeig/Lightning-VFX-WebGL](https://github.com/MirzaBeig/Lightning-VFX-WebGL) (cloned into each sandbox at run time; not included in this repo)
- Sandbox infra: [islo.dev](https://islo.dev/)
- Pattern: pokeloop + meta-harness-on-islo, both by [Yossi Eliaz](https://github.com/zozo123)
- Movie: [`agentreel`](https://github.com/islo-labs/agentreel)

## License

MIT for the code in this repo; see [`LICENSE`](./LICENSE). The Unity scene belongs to its author and is not covered by this license.
