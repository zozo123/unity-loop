"""Spawn an islo sandbox serving Unity + one variant. Returns its public share URL.

Reuses an existing sandbox name if it exists (idempotent) — fast path for loop mode.
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISLO = os.environ.get("ISLO_BIN", "islo")


def render_template(variant: dict) -> str:
    tpl = (ROOT / "unity" / "template.html").read_text()
    title = variant.get("title", "Lightning VFX")
    bg = variant.get("bg", "#000")
    flt = variant.get("filter", "none")
    frame_color = variant.get("frame_color", "#ff006e")
    frame_glow = variant.get("frame_glow", "0 0 40px #ff006e88")
    return (tpl
        .replace("{{TITLE}}", title)
        .replace("{{BG}}", bg)
        .replace("{{FILTER}}", flt)
        .replace("{{FRAME_COLOR}}", frame_color)
        .replace("{{FRAME_GLOW}}", frame_glow))


def spawn_variant(name: str, variant: dict) -> str:
    """Provision (or reuse) an islo sandbox, push the variant HTML, start Caddy, share port 8080."""
    html = render_template(variant)
    # Push the rendered template by writing it through `islo use -- bash -c`
    # The sandbox already has Lightning-VFX-WebGL/ cloned from islo.yaml's `sources`.
    script = f"""set -e
mkdir -p /workspace/site
cp -n /workspace/Lightning-VFX-WebGL/Build /workspace/site/Build 2>/dev/null || \
  ln -sfn /workspace/Lightning-VFX-WebGL/Build /workspace/site/Build
ln -sfn /workspace/Lightning-VFX-WebGL/TemplateData /workspace/site/TemplateData 2>/dev/null || true
cat > /workspace/site/index.html <<'__VARIANT_HTML__'
{html}
__VARIANT_HTML__
cat > /workspace/Caddyfile <<'__CADDY__'
{{ auto_https off; admin off }}
:8080 {{
    root * /workspace/site
    @uw path *.unityweb
    header @uw Content-Encoding gzip
    header @uw Vary Accept-Encoding
    @wasm path *.wasm.unityweb *.wasm
    header @wasm Content-Type application/wasm
    @data path *.data.unityweb
    header @data Content-Type application/octet-stream
    @fwjs path *.framework.js.unityweb
    header @fwjs Content-Type application/javascript
    header {{
        Cross-Origin-Opener-Policy "same-origin"
        Cross-Origin-Embedder-Policy "require-corp"
        Cross-Origin-Resource-Policy "cross-origin"
        Access-Control-Allow-Origin "*"
    }}
    file_server
}}
__CADDY__
pkill -f 'caddy run' 2>/dev/null || true
sleep 1
setsid -f caddy run --config /workspace/Caddyfile --adapter caddyfile </dev/null >/tmp/caddy.log 2>&1
sleep 2
curl -sf -o /dev/null http://localhost:8080/ && echo OK
"""
    # Use ISLO from any cwd that lacks islo.yaml conflicts
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [ISLO, "use", name, "--source", "github://MirzaBeig/Lightning-VFX-WebGL", "--", "bash", "-c", script],
            cwd=td, check=True,
        )
        share = subprocess.check_output(
            [ISLO, "share", name, "8080", "--ttl", "24h", "-o", "json"],
            cwd=td,
        )
    info = json.loads(share)
    return info.get("url") or info.get("URL") or json.dumps(info)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "arena-debug"
    variant = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {"title": "DEBUG", "bg": "#101"}
    print(spawn_variant(name, variant))
