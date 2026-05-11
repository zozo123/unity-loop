"""Claude-vision judge: screenshot a variant URL, score 0..5 vs target prompt."""
from __future__ import annotations
import base64, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def screenshot(url: str, out_png: Path) -> None:
    """Headless screenshot. Tries playwright; falls back to chromium --headless."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1280, "height": 720})
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(3_000)  # let Unity render a few frames
            page.screenshot(path=str(out_png), full_page=False)
            b.close()
            return
    except Exception:
        pass
    subprocess.check_call([
        "chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        f"--window-size=1280,720", f"--screenshot={out_png}", url,
    ])


def judge_variant(url: str, target_prompt: str, run_dir: Path) -> float:
    import anthropic  # type: ignore
    shot = run_dir / f"shot-{os.urandom(3).hex()}.png"
    screenshot(url, shot)
    img_b64 = base64.b64encode(shot.read_bytes()).decode()
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=(
            "You judge how well a UI screenshot matches a target aesthetic. "
            "Reply ONLY with JSON: {\"score\": float 0..5, \"reason\": short string}."
        ),
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                {"type": "text", "text": f"Target aesthetic:\n{target_prompt}\n\nScore this screenshot."},
            ],
        }],
    )
    out = msg.content[0].text.strip()
    try:
        return float(json.loads(out)["score"])
    except Exception:
        # Last-resort heuristic — never crash the loop
        return 2.5


if __name__ == "__main__":
    # bin/unity-loop eval <url> <task>
    url, task = sys.argv[1], sys.argv[2]
    prompt = (ROOT / "tasks" / task / "prompt.md").read_text()
    run_dir = ROOT / "runs" / "_manual"
    run_dir.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"score": judge_variant(url, prompt, run_dir)}))
