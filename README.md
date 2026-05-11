# unity-loop

**How AI vibes Unity on [islo.dev](https://islo.dev/) sandboxes — Claude-vision tournament over presentation variants.**

> **Project page:** https://zozo123.github.io/unity-loop-page/
>
> **Live champion:** [https://ssotep9384qyc19npfpqg8h7q.share.islo.dev](https://ssotep9384qyc19npfpqg8h7q.share.islo.dev) (24h islo share — refresh from `runs/champion.json`)
>
> **Writeup:** [`docs/POST.md`](./docs/POST.md)
>
> **Built on:** [islo.dev](https://islo.dev/) — agent sandboxes with snapshots, shares, gateway egress.
>
> **Inspired by:** [pokeloop](https://github.com/zozo123/pokeloop) (GA over LLM policies), [meta-harness-on-islo](https://github.com/zozo123/meta-harness-on-islo) (proposer/eval loop).

---

## What this is

A bandit-search loop where Claude *vibes* the presentation of a Unity WebGL scene. Each variant is a JSON spec of CSS + page chrome wrapped around a fixed Unity build. N islo sandboxes serve N variants in parallel. Claude (vision) judges screenshots against a target prompt. Winner is promoted to the gh-pages champion.

**The Unity wasm is fixed** — Lightning VFX by [@MirzaBeig](https://github.com/MirzaBeig/Lightning-VFX-WebGL). Variation lives in the wrapper. That's the honest thing to do without a 10GB Unity Editor image; rebuilding `.wasm` inside the sandbox is a separate ticket ([`docs/POST.md#tier-3`](./docs/POST.md#tier-3-real-unity-editor-rebuilds)).

## Quick start (offline, deterministic — ~5s)

```bash
bin/unity-loop demo            # 6-round canned trajectory, 1.2 → 4.8 score
bin/unity-loop viz             # serve the dashboard
# open http://localhost:8765
```

You should see scores climb **1.2 → 2.4 → 3.1 → 3.7 → 4.4 → 4.8** for task `synthwave`, with the converging variant rendered live.

## Real run (Claude API + N islo sandboxes)

```bash
export ANTHROPIC_API_KEY=...
bin/unity-loop loop --task synthwave --k 4 --steps 6
```

Spawns K islo sandboxes (one per variant), each serving Unity + variant CSS via Caddy, calls Claude vision for the judge round, writes `runs/<run-id>/`, updates `runs/champion.json`. The page repo's CI re-deploys gh-pages on champion change.

## Layout (mirrors meta-harness-on-islo)

```
islo.yaml             base sandbox config
tasks/<name>/         prompt.md (target aesthetic)
harness/v<N>/         system.md + proposer template
bin/unity-loop        orchestrator (eval | propose | loop | viz | demo)
bin/proposer.py       reads runs/, asks Claude for next variant
bin/judge.py          Claude-vision scoring of screenshots
bin/host.py           spawns islo sandbox, templates variant, shares port
bin/agent_sim.py      deterministic offline agent stand-in (for `demo`)
unity/template.html   Unity host with {{VARIANT_CSS}} + {{VARIANT_HTML}} slots
unity/Caddyfile       precompressed gzip + COOP/COEP + application/wasm
viz/index.html        single-file dashboard (timeline + variants + judge trace)
runs/                 populated by the loop; runs/champion.json drives the page
```

## Credits

- Unity scene: [MirzaBeig/Lightning-VFX-WebGL](https://github.com/MirzaBeig/Lightning-VFX-WebGL)
- Sandbox infra: [islo.dev](https://islo.dev/)
- Pattern: pokeloop + meta-harness-on-islo, both by [@zozo123](https://github.com/zozo123)
- Movie: [`agentreel`](https://github.com/islo-labs/agentreel)

MIT.
