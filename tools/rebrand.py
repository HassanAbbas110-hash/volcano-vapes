"""Rebrand the site for a new shop in one go.

    python tools/rebrand.py new-brand.json

new-brand.json has the same fields as brand.json (the current brand). The script:
  1. swaps every old brand detail (name, address, phone, partner...) for the new one in the pages,
     assets/site.js, assets/site.css and tools/snapshot.py (product data is left alone),
  2. sets the CONFIG values in assets/site.js (social links, partner, online store, hours),
  3. recolours the theme: every colour near the old accent's hue moves to the new accent's hue,
  4. converts any images listed under "images" (logo, shopfront, interior, disposables, eliquids),
  5. saves the new details as brand.json and checks nothing of the old brand is left.
Run it again with another file to rebrand again."""
import colorsys, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_KEYS = ["name", "short", "domain", "email", "phone", "whatsapp", "street", "centre", "road", "town", "postcode", "province", "partnerName"]
CONFIG_KEYS = ["instagram", "facebook", "partnerName", "partnerUrl", "onlineStore", "hoursNote"]
# target size (w, h) per photo, matching the layout's aspect ratios
PHOTOS = {"shopfront": (900, 874), "interior": (900, 506), "disposables": (900, 1193), "eliquids": (900, 1028)}

def files():
    out = sorted(ROOT.glob("*.html")) + [ROOT / "assets/site.js", ROOT / "assets/site.css", ROOT / "tools/snapshot.py"]
    return [f for f in out if f.exists()]

def hls(hexstr):
    h = hexstr.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)

def recolour(text, old_accent, new_accent):
    oh, ol, os_ = hls(old_accent); nh, nl, ns = hls(new_accent)
    def shift(r, g, b):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < 0.25 or min(abs(h - oh), 1 - abs(h - oh)) > 20 / 360:
            return None  # not part of the accent family (greys, WhatsApp green, Instagram pink...)
        s = min(1, s * (ns / os_ if os_ else 1))
        l = l * nl / ol if l <= ol else 1 - (1 - l) * (1 - nl) / (1 - ol)
        return [round(v * 255) for v in colorsys.hls_to_rgb(nh, max(0, min(1, l)), s)]
    def hex_sub(m):
        h = m.group(0)[1:]; new = shift(*(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        return m.group(0) if new is None else "#" + "".join(f"{v:02x}" for v in new)
    def rgb_sub(m):
        new = shift(*map(int, m.group(2, 3, 4)))
        return m.group(0) if new is None else f"{m.group(1)}({new[0]},{new[1]},{new[2]}"
    text = re.sub(r"#[0-9a-fA-F]{6}\b", hex_sub, text)
    return re.sub(r"(rgba?)\((\d+),\s*(\d+),\s*(\d+)", rgb_sub, text)

def images(spec):
    from PIL import Image  # only needed when images are given
    img = ROOT / "assets/img"
    if spec.get("logo"):
        lg = Image.open(spec["logo"]).convert("RGBA")
        for name, w in (("logo.webp", 420), ("logo-sm.webp", 180)):
            lg.resize((w, round(lg.height * w / lg.width)), Image.LANCZOS).save(img / name, quality=90)
        side = max(lg.size); sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.paste(lg, ((side - lg.width) // 2, (side - lg.height) // 2)); sq.resize((192, 192), Image.LANCZOS).save(img / "icon.png")
        print("  logo -> logo.webp, logo-sm.webp, icon.png")
    for key, (w, h) in PHOTOS.items():
        if not spec.get(key): continue
        im = Image.open(spec[key]).convert("RGB")
        scale = max(w / im.width, h / im.height)  # cover, then centre-crop
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        x, y = (im.width - w) // 2, (im.height - h) // 2
        im.crop((x, y, x + w, y + h)).save(img / f"{key}.webp", quality=82)
        print(f"  {key} -> {key}.webp ({w}x{h})")

def main(path):
    old = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
    new = {**old, **json.loads(pathlib.Path(path).read_text(encoding="utf-8"))}
    pairs = sorted(((old[k], new[k]) for k in TEXT_KEYS if old.get(k) and new.get(k) and old[k] != new[k]), key=lambda p: -len(p[0]))
    print("Text swaps:"); [print(f"  {a!r} -> {b!r}") for a, b in pairs]
    for f in files():
        s = t = f.read_text(encoding="utf-8")
        # two passes through placeholders, so a new value that contains an old one isn't swapped twice
        for i, (a, _) in enumerate(pairs): t = t.replace(a, f"\x00{i}\x00")
        for i, (_, b) in enumerate(pairs): t = t.replace(f"\x00{i}\x00", b)
        if f.name == "site.js":
            for k in CONFIG_KEYS:
                t, n = re.subn(rf'(\n\s*{k}:\s*)"[^"]*"', lambda m: m.group(1) + json.dumps(new.get(k, "")), t, count=1)
                assert n == 1, f"CONFIG.{k} not found in site.js"
        if f.suffix in (".css", ".html") and new["accent"].lower() != old["accent"].lower():
            t = recolour(t, old["accent"], new["accent"])
        if t != s: f.write_text(t, encoding="utf-8"); print(f"  updated {f.relative_to(ROOT)}")
    if new.get("images"): print("Images:"); images(new["images"])
    # check: nothing of the old brand left behind
    new_text = " ".join(str(new.get(k, "")) for k in TEXT_KEYS)
    left = [(f.relative_to(ROOT), a) for f in files() for a, _ in pairs if a not in new_text and a in f.read_text(encoding="utf-8")]
    for f, a in left: print(f"  STILL FOUND {a!r} in {f}")
    assert not left, "some old brand details were not replaced"
    saved = {**new, "images": {}}
    (ROOT / "brand.json").write_text(json.dumps(saved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Done. brand.json now holds the new brand.")

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
