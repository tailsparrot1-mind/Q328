#!/usr/bin/env python3
"""Build a separate Vkus 3.28 marketplace candidate from the immutable release ZIP."""
from __future__ import annotations
import hashlib, io, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
OUTER = ROOT / "recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip"
BASE = "https://raw.githubusercontent.com/tailsparrot1-mind/vkus--3.17-button/feature/supabase-marketplace-client/"
FILES = {
    "vkus/cloud_marketplace.py": "vkus/cloud_marketplace.py",
    "vkus/exchange_marketplace.py": "vkus/exchange_marketplace.py",
    "tests/test_cloud_marketplace.py": "tests/test_cloud_marketplace.py",
}
def download(path: str) -> bytes:
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"Vkus-328-build"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def main():
    if not OUTER.is_file():
        raise SystemExit(f"Missing immutable source archive: {OUTER}")
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTER) as z:
        names = z.namelist()
        prefix = next((n[:-len("main.py")] for n in names if n.endswith("main.py")), None)
        if prefix is None:
            raise SystemExit("Nested source archive does not contain main.py")
        files = {n[len(prefix):]: z.read(n) for n in names if n.startswith(prefix) and not n.endswith("/")}
    app_path = "vkus/app.py"
    app = files[app_path].decode("utf-8")
    marker = "        if 1360 <= x <= 1618 and 373 <= y <= 700:\n"
    hook = (
        "        if 1130 <= x <= 1385 and 87 <= y <= 133:\n"
        "            from .exchange_marketplace import open_cloud_marketplace_window\n"
        "            open_cloud_marketplace_window(self.root)\n"
        "            return\n"
    )
    if "open_cloud_marketplace_window(self.root)" not in app:
        if marker not in app:
            raise SystemExit("Could not locate known Exchange click handler in Vkus 3.28; refusing a fuzzy patch.")
        app = app.replace(marker, hook + marker, 1)
        files[app_path] = app.encode("utf-8")
    visual_path = "vkus/exchange_visual.py"
    visual = files[visual_path].decode("utf-8")
    old_subtitle = '"Находите целевую аудиторию и потенциальных покупателей для любой ниши",\n          18, "#e4eaff", width=980, fit=True)'
    new_subtitle = '"Находите целевую аудиторию и потенциальных покупателей для любой ниши",\n          18, "#e4eaff", width=800, fit=True)\n    rounded(1130, 87, 1385, 133, "#21104d", "#9c35ff", 12, 1)\n    label(1257, 96, "Доска объявлений", 11, "#f2dfff", "bold", "center", width=230, fit=True)\n    label(1257, 113, "Ищу  ·  Предлагаю", 8, "#c7b0ef", "normal", "center", width=220, fit=True)'
    if old_subtitle not in visual:
        raise SystemExit("Could not locate Vkus 3.28 Birzha subtitle; refusing an uncertain visual patch.")
    visual = visual.replace(old_subtitle, new_subtitle, 1)
    files[visual_path] = visual.encode("utf-8")
    for target, source in FILES.items():
        files[target] = download(source)
    req = files.get("requirements.txt", b"").decode("utf-8")
    if "keyring" not in req:
        files["requirements.txt"] = (req.rstrip() + "\nkeyring>=25.2\n").encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            z.writestr(name, data)
    candidate = OUT / "Vkus_3.28_Marketplace_Candidate.zip"
    candidate.write_bytes(buf.getvalue())
    sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    (OUT / "SHA256SUMS.txt").write_text(f"{sha}  {candidate.name}\n", encoding="utf-8")
    (OUT / "BUILD_NOTES.md").write_text(
        "# Vkus 3.28 — Marketplace candidate\n\n"
        "- Base: immutable recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip.\n"
        "- Added Supabase client and marketplace UI module from reviewed feature branch.\n"
        "- Connected existing Birzha CTA to cloud noticeboard window.\n"
        "- Original archive and Supabase database were not modified.\n"
        "- Real multi-user signup/login and listing exchange still require manual account smoke tests.\n"
        f"- SHA-256: {sha}\n", encoding="utf-8")
    print(f"BUILT {candidate} ({candidate.stat().st_size} bytes)")
    print(f"SHA256 {sha}")
if __name__ == "__main__":
    main()
