"""Refresh assets/products.json from Volcano Vapes' live Shopify store (in-stock only).
Run: python tools/snapshot.py   (or pass a folder of saved products.json pages to skip downloading)

Writes the same shape the site already reads, plus:
  vid  first in-stock variant id (Shopify cart links: /cart/<vid>:<qty>)
  var  True when there's more than one in-stock option (flavour, colour, strength)
and per product in assets/details/: i (big image), d (description), a (specs), v (variants: [id, title, price]), o (option name)."""
import json, re, html, sys, glob, urllib.request, pathlib, datetime

STORE = "https://volcanovapes.co.za"
SHARDS = 40  # must match DETAIL_SHARDS in assets/site.js
NEW_DAYS = 45
# Left out on purpose: cannabis/THC/CBD lines, bongs, drinks and gift cards. Remove a type here to list it.
SKIP_TYPES = {"thc disposable", "edibles", "bong", "tincture", "pet cbd", "wellness patches", "soda", "energy drink", "water", "gift card"}
SKIP_VENDORS = {"reina", "awaken"}  # 510 / THC cartridge brands
SKIP_WORDS = re.compile(r"\b(thc|cbd|cannabis|strain|beer funnel|suip pyp)\b", re.I)

# Shopify product_type -> (main, sub). Subs reuse the template's names where one exists.
TYPES = {
    "disposables": ("vape", "Disposables"),
    "flavour pod": ("vape", "Prefilled Pods"), "pods & cartridges": ("vape", "Prefilled Pods"),
    "pod system": ("vape", "Devices"), "device": ("vape", "Devices"), "pod kits": ("vape", "Devices"),
    "salt nic eliquid": ("vape", "Nic Salts"), "salt nic e-liquid": ("vape", "Nic Salts"),
    "freebase e-liquid": ("vape", "E Liquids"),
    "longfills": ("vape", "Longfills & Shots"), "flavour shots": ("vape", "Longfills & Shots"), "nicotine shot": ("vape", "Longfills & Shots"),
    "replacement pod": ("vape", "Coils, Pods & Tanks"), "coil": ("vape", "Coils, Pods & Tanks"), "cartridge": ("vape", "Coils, Pods & Tanks"),
    "tank": ("vape", "Coils, Pods & Tanks"), "cotton": ("vape", "Coils, Pods & Tanks"),
    "battery": ("vape", "Batteries & Chargers"), "batteries": ("vape", "Batteries & Chargers"),
    "accessories": ("vape", "Vape Accessories"), "merchandise": ("vape", "Vape Accessories"),
    "nicotine pouch": ("snus", "Snus"), "nicotine pouches": ("snus", "Snus"), "nicotine strip": ("snus", "Snus"),
    "nicotine pearls": ("snus", "Snus"), "caffeine pouch": ("snus", "Snus"), "nasal tobacco": ("snus", "Snuff"),
    "cigars": ("tobacco", "Cigars & Tobacco"), "cigar accessories": ("tobacco", "Cigars & Tobacco"), "pipe tobacco": ("tobacco", "Cigars & Tobacco"),
}

def guess(p):
    """Products with no type: decide from tags, then the name."""
    t = " ".join(p["tags"]).lower() + " " + p["title"].lower()
    for words, cat in ((("snus",), ("snus", "Snus")), (("flavour shot", "longfill", "longill"), ("vape", "Longfills & Shots")),
                       (("saltnic", "nic salt"), ("vape", "Nic Salts")), (("freebase",), ("vape", "E Liquids")),
                       (("coil", "replacement pod", "pod cartridge", "cartridges", " pods", "pod replacement", "mesh pod"), ("vape", "Coils, Pods & Tanks")),
                       (("disposable", "puff"), ("vape", "Disposables")), (("battery",), ("vape", "Batteries & Chargers")),
                       (("cotton", "hardware"), ("vape", "Coils, Pods & Tanks"))):
        if any(w in t for w in words): return cat
    return ("vape", "Vape Accessories")

def pages():
    if len(sys.argv) > 1:
        for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
            yield json.load(open(f, encoding="utf-8"))["products"]
        return
    for n in range(1, 100):
        req = urllib.request.Request(f"{STORE}/products.json?limit=250&page={n}", headers={"User-Agent": "Mozilla/5.0"})
        batch = json.load(urllib.request.urlopen(req, timeout=60))["products"]
        if not batch: return
        yield batch

def text(h, cap):
    t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[\s\S]*?</\1>", "", h or "")))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= cap else t[:cap].rsplit(" ", 1)[0] + "…"

def sized(src, w):
    return f"{src}{'&' if '?' in src else '?'}width={w}" if src else ""

raw = [p for batch in pages() for p in batch]
vendors = sorted({p["vendor"] for p in raw if p["vendor"] and p["vendor"].lower() != "volcanovapes"}, key=len, reverse=True)
def brand(p):
    if p["vendor"] and p["vendor"].lower() != "volcanovapes": return p["vendor"]
    title = p["title"].lower().replace(" ", "")
    return next((v for v in vendors if title.startswith(v.lower().replace(" ", ""))), "")

now = datetime.datetime.now(datetime.timezone.utc)
out, details, skipped = [], {}, 0
for p in raw:
    ptype = (p["product_type"] or "").strip().lower()
    if ptype in SKIP_TYPES or p["vendor"].lower() in SKIP_VENDORS or SKIP_WORDS.search(p["title"] + " " + " ".join(p["tags"])):
        skipped += 1; continue
    live = [v for v in p["variants"] if v["available"] and 0 < float(v["price"]) < 100000]
    if not live: continue
    main, sub = TYPES.get(ptype) or guess(p)
    name = html.unescape(p["title"]).strip()
    prices = [float(v["price"]) for v in live]
    puffs = re.search(r"(\d{1,3}(?:[ ,]\d{3})+|\d+(?:\.\d+)?)\s*k?\s*puffs?", name, re.I)
    mg = re.search(r"(\d+(?:\.\d+)?)\s*mg", name, re.I)
    img = p["images"][0]["src"] if p["images"] else ""
    multi = len(live) > 1 and not (len(live) == 1 or live[0]["title"] == "Default Title")
    opt = p["options"][0]["name"].strip().capitalize() if p.get("options") else ""
    if opt.lower() in ("title", ""): opt = "Option"
    details[p["id"]] = {
        "i": sized(img, 1000), "d": text(p["body_html"], 700), "a": {},
        "v": [[v["id"], v["title"], float(v["price"])] for v in live] if multi else [], "o": opt,
    }
    published = datetime.datetime.fromisoformat(p["published_at"]) if p.get("published_at") else None
    out.append({
        "id": p["id"], "n": name, "p": min(prices), "c": main, "s": sub, "b": brand(p),
        "t": sized(img, 360), "u": f"{STORE}/products/{p['handle']}", "vid": live[0]["id"],
        "new": bool(published and (now - published).days <= NEW_DAYS), "var": multi,
        "puffs": re.sub(r"[ ,]", "", puffs.group(1)) if puffs else "", "mg": mg.group(1) if mg else "",
    })

assert len(out) > 100, f"only {len(out)} products; is the store feed down?"
assert all(o["p"] > 0 and o["vid"] for o in out), "every product needs a price and a variant id"
out.sort(key=lambda o: (not o["new"], not o["t"], o["n"]))
path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "products.json"
path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
# details are sharded so a product page only downloads ~1/40th of them
ddir = path.parent / "details"; ddir.mkdir(exist_ok=True)
for old in ddir.glob("*.json"): old.unlink()
for k in range(SHARDS):
    part = {i: v for i, v in details.items() if i % SHARDS == k}
    (ddir / f"{k}.json").write_text(json.dumps(part, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"{len(out)} in-stock products -> {path.name} ({path.stat().st_size // 1024} KB) + {SHARDS} detail shards; {skipped} left out (see SKIP_*)")
