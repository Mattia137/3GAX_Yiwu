"""Build `Yiwu Elevation Growth Lab.html` from app_template.html.

Reads the site lines and the atlas figure library from `Yiwu Podium Lab.html`, and the twelve
figure-ground plates from `Yiwu Urban Fabric Atlas.html`, and writes them into the template as one
JSON block. Run from anywhere:  python build.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "Yiwu Elevation Growth Lab.html"


def source(name):
    return (HERE / name).read_text(encoding="utf8")


def block(html, el_id):
    m = re.search(r'id="%s">(.*?)</script>' % el_id, html, re.S)
    return json.loads(m.group(1))


def path_rings(d, flip_h=None):
    """SVG path 'M x yL x y...Z' (y down) -> rings [[x,y],...] (y up when flip_h is given)."""
    rings = []
    for part in re.findall(r"M([^Z]*)Z", d):
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", part)]
        pts = [[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)]
        if flip_h is not None:
            pts = [[x, round(flip_h - y, 1)] for x, y in pts]
        if len(pts) >= 3:
            rings.append(pts)
    return rings


def main():
    pod = block(source("Yiwu Podium Lab.html"), "site-data")
    atlas = block(source("Yiwu Urban Fabric Atlas.html"), "atlas-data")

    names = {
        "village": "Village cluster", "siceng": "Si Ceng Ban field", "resettle": "Resettlement rows",
        "megablock": "Trade City megablock", "sheds": "Market sheds + rows", "courtyard": "Workshop compound grid",
        "factory": "Factory shed field", "logistics": "Logistics park", "highrise": "High-rise estate",
        "cbd": "Business district", "campus": "School campus", "wetland": "Wetland field",
    }
    fabric = []
    for f in atlas["fabric"]:
        rings = path_rings(f["d"], flip_h=800.0)
        fabric.append({"key": f["key"], "n": names.get(f["key"], f["key"]), "cov": f.get("cov"), "rings": rings})

    data = {
        "site": {k: pod[k] for k in ("redline", "ctrlPodium", "ctrlHigh", "green")},
        "lib": pod["lib"],
        "fabric": fabric,
    }
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    tpl = (HERE / "app_template.html").read_text(encoding="utf8")
    out = tpl.replace("/*__DATA__*/{}", js)
    assert out != tpl, "data marker missing from template"
    # base settings: the page starts from these (every setting, genome and painted density), if the file is here
    base = HERE / "base_settings.json"
    if base.exists():
        bjs = json.dumps(json.loads(base.read_text(encoding="utf8")), separators=(",", ":"), ensure_ascii=False)
        out = out.replace("/*__BASE__*/null", bjs)
    OUT.write_text(out, encoding="utf8")
    print(f"wrote {OUT.name}: {len(out)/1e6:.2f} MB · {len(data['lib'])} figures · "
          f"{'base settings · ' if base.exists() else ''}"
          f"{len(fabric)} plates · {sum(len(f['rings']) for f in fabric)} plate figures")


if __name__ == "__main__":
    main()
