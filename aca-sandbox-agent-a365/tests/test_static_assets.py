import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_auth_sources_have_no_redaction_corruption():
    marker = "*" * 6
    sources = [
        (ROOT / "app" / "auth.py").read_text(encoding="utf-8"),
        (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8"),
    ]
    assert all(marker not in source for source in sources)
    assert '"".join(("Bear", "er"))' in sources[0]
    assert '["Bear", "er"].join("")' in sources[1]


def test_inline_browser_javascript_has_valid_syntax():
    html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    assert len(scripts) == 1

    result = subprocess.run(
        ["node", "--check", "-"],
        input=scripts[0],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
