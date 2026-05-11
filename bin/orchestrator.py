"""unity-loop orchestrator.

Two modes:
  demo  — deterministic offline trajectory, writes runs/<id>/ + champion.json
  loop  — real Claude API + parallel islo sandboxes

Pattern: K variants per round → judge → keep top-1 → propose next K → repeat.
"""
from __future__ import annotations
import argparse, json, os, random, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
TASKS = ROOT / "tasks"


def new_run_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def write_state(run_dir: Path, state: dict) -> None:
    (run_dir / "state.json").write_text(json.dumps(state, indent=2))


def champion(run_dir: Path, variant: dict, score: float, share_url: str | None) -> None:
    payload = {
        "ts": time.time(),
        "run": run_dir.name,
        "score": score,
        "variant": variant,
        "share_url": share_url,
    }
    (RUNS / "champion.json").write_text(json.dumps(payload, indent=2))


# ── demo mode: deterministic, no network ────────────────────────────────────
DEMO_TRAJECTORY = [
    {"step": 0, "score": 1.2, "variant": {"bg": "#222", "filter": "none", "title": "Lightning VFX"}},
    {"step": 1, "score": 2.4, "variant": {"bg": "linear-gradient(180deg,#1a0033,#000)", "filter": "saturate(1.2)", "title": "Storm"}},
    {"step": 2, "score": 3.1, "variant": {"bg": "linear-gradient(180deg,#ff006e22,#000)", "filter": "saturate(1.4) hue-rotate(-10deg)", "title": "Neon Storm"}},
    {"step": 3, "score": 3.7, "variant": {"bg": "linear-gradient(180deg,#ff006e44,#3a86ff22 50%,#000)", "filter": "saturate(1.8) hue-rotate(-20deg) contrast(1.1)", "title": "SYNTHWAVE"}},
    {"step": 4, "score": 4.4, "variant": {"bg": "linear-gradient(180deg,#ff006e,#8338ec 40%,#3a86ff 70%,#000)", "filter": "saturate(2.0) hue-rotate(-30deg) contrast(1.2)", "title": "SYNTHWAVE //"}},
    {"step": 5, "score": 4.8, "variant": {"bg": "linear-gradient(180deg,#ff006e,#8338ec 35%,#3a86ff 65%,#06002a)", "filter": "saturate(2.2) hue-rotate(-30deg) contrast(1.25) brightness(1.05)", "title": "S Y N T H W A V E //"}},
]


def cmd_demo(args) -> int:
    del args  # demo is parameterless
    run_id = new_run_id()
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {"task": "synthwave", "k": 4, "steps": len(DEMO_TRAJECTORY), "trajectory": []}

    print(f"→ demo run: {run_id}")
    print(f"→ task: synthwave  k=4  steps={len(DEMO_TRAJECTORY)}")
    print()

    rng = random.Random(42)
    for entry in DEMO_TRAJECTORY:
        # simulate K-1 losers around the winner
        losers = []
        for _ in range(3):
            losers.append({
                "variant": dict(entry["variant"]),
                "score": max(0.0, entry["score"] - rng.uniform(0.4, 1.6)),
            })
        winner = {"variant": entry["variant"], "score": entry["score"]}
        round_data = {
            "step": entry["step"],
            "winner": winner,
            "losers": losers,
            "judge_reason": f"saturation and color story align with 'synthwave' (score {entry['score']:.1f}/5)",
        }
        state["trajectory"].append(round_data)
        write_state(run_dir, state)
        bar = "█" * int(entry["score"] * 4) + "░" * (20 - int(entry["score"] * 4))
        print(f"  step {entry['step']}  score {entry['score']:.1f}/5  {bar}  {entry['variant']['title']}")
        time.sleep(0.4)

    final = DEMO_TRAJECTORY[-1]
    champion(run_dir, final["variant"], final["score"], share_url=None)
    print()
    print(f"✓ champion: {final['variant']['title']}  ({final['score']}/5)")
    print(f"✓ state:    runs/{run_id}/state.json")
    print(f"✓ champion: runs/champion.json")
    print(f"→ next: bin/unity-loop viz  (open http://localhost:8765)")
    return 0


# ── real loop mode ──────────────────────────────────────────────────────────
def cmd_loop(args) -> int:
    try:
        from judge import judge_variant  # noqa
        from proposer import propose_next  # noqa
        from host import spawn_variant  # noqa
    except Exception:
        # Defer import errors until actually running real mode
        sys.path.insert(0, str(ROOT / "bin"))
        from judge import judge_variant  # type: ignore
        from proposer import propose_next  # type: ignore
        from host import spawn_variant  # type: ignore

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY required for real loop mode", file=sys.stderr)
        return 2

    task_dir = TASKS / args.task
    if not task_dir.exists():
        print(f"no such task: {args.task}", file=sys.stderr); return 2
    target_prompt = (task_dir / "prompt.md").read_text()

    run_id = new_run_id()
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {"task": args.task, "k": args.k, "steps": args.steps, "trajectory": []}

    print(f"→ loop run: {run_id}  task={args.task}  k={args.k}  steps={args.steps}")

    history: list[dict] = []
    for step in range(args.steps):
        # propose K variants
        variants = [propose_next(target_prompt, history) for _ in range(args.k)]
        # spawn each in a sandbox
        urls = [spawn_variant(f"arena-{run_id}-{step}-{i}", v) for i, v in enumerate(variants)]
        # judge each
        scored = [
            {"variant": v, "score": judge_variant(url, target_prompt, run_dir), "url": url}
            for v, url in zip(variants, urls)
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        winner, losers = scored[0], scored[1:]
        history.append(winner)
        state["trajectory"].append({"step": step, "winner": winner, "losers": losers})
        write_state(run_dir, state)
        champion(run_dir, winner["variant"], winner["score"], share_url=winner["url"])
        print(f"  step {step}  best {winner['score']:.2f}/5  → {winner['url']}")

    print(f"\n✓ done. runs/{run_id}/state.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    lp = sub.add_parser("loop")
    lp.add_argument("--task", default="synthwave")
    lp.add_argument("--k", type=int, default=4)
    lp.add_argument("--steps", type=int, default=6)
    args = ap.parse_args()
    return cmd_demo(args) if args.cmd == "demo" else cmd_loop(args)


if __name__ == "__main__":
    sys.exit(main())
