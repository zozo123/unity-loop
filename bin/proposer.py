"""Claude proposer: given history of (variant, score), emit next variant JSON."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = (ROOT / "harness" / "v0" / "system.md").read_text() if (ROOT / "harness" / "v0" / "system.md").exists() else ""


def propose_next(target_prompt: str, history: list[dict]) -> dict:
    import anthropic  # type: ignore
    client = anthropic.Anthropic()
    hist_text = "\n".join(
        f"- score {h['score']:.2f}  variant: {json.dumps(h['variant'])}"
        for h in history[-8:]
    ) or "(no history yet)"
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=SYSTEM or "Propose CSS-only variants of a Unity webpage wrapper.",
        messages=[{
            "role": "user",
            "content": (
                f"Target aesthetic:\n{target_prompt}\n\n"
                f"History (best variants so far, with scores 0..5):\n{hist_text}\n\n"
                "Emit the NEXT variant as JSON only. Keys: "
                "bg (CSS background), filter (CSS canvas filter), title (string), "
                "frame_color (hex), frame_glow (CSS box-shadow)."
            ),
        }],
    )
    raw = msg.content[0].text.strip()
    # Tolerate fenced JSON
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[1].rsplit("\n", 1)[0]
        if raw.startswith("json\n"): raw = raw[5:]
    return json.loads(raw)


if __name__ == "__main__":
    _ = Path  # keep Path import for type hint clarity
    print(json.dumps(propose_next("synthwave neon", []), indent=2))
