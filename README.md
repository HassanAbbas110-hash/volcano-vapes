# Pro Vape Shop Site (template)

Built for Cloudside Vapor (Boksburg). Use this folder as the base for every new vape shop. **Copy it first; never edit this folder for a new client.**

Plain HTML/CSS/JS, no build step. It works on any static host (GitHub Pages, Netlify).

## Pages
| File | What it is |
|---|---|
| `index.html` | Home: hero, categories, new arrivals, vape finder quiz, coil finder banner, ways to get it, brands, shop photos, reviews and socials |
| `shop.html` | Full catalogue with filters (category, brand, flavour, puffs, price, pouch strength) |
| `product.html` | Product page (`?id=`), with what fits / fits these devices, related, recently viewed |
| `fit.html` | Coil & Pod Finder (`?d=xros`) |
| `about.html`, `visit.html`, `help.html` | About, map and contact, delivery and FAQs |

## Files you change for a new shop
| File | What's in it |
|---|---|
| `brand.json` | Current brand details. **Don't hand-edit it**: write a new file and run the rebrand script |
| `tools/rebrand.py` | Swaps every brand detail, recolours the theme from one accent colour, converts the logo and photos |
| `assets/img/` | `logo.webp`, `logo-sm.webp`, `icon.png`, `shopfront.webp`, `interior.webp`, `disposables.webp`, `eliquids.webp` (made by the rebrand script) |
| `assets/site.js` → `CONFIG` | Hours note, socials, delivery partner, online store (set by the rebrand script) |
| Page copy | Hero line, About story, meta descriptions. Rewrite by hand from the shop's real facts |

## Rebrand in one command
1. Write `new-brand.json` (any field you leave out keeps its current value):
```json
{
  "name": "Blue Haze Vapes", "short": "Blue Haze",
  "domain": "bluehaze.co.za", "email": "hello@bluehaze.co.za",
  "phone": "+27 82 111 2222", "whatsapp": "27821112222",
  "street": "12 Main Road", "centre": "Eastgate Mall", "road": "Bradford Road",
  "town": "Bedfordview", "postcode": "2008", "province": "Gauteng",
  "hoursNote": "Open 7 days a week",
  "instagram": "", "facebook": "",
  "partnerName": "", "partnerUrl": "",
  "onlineStore": "",
  "accent": "#1e7bff",
  "images": { "logo": "path/to/logo.png", "shopfront": "path/to/front.jpg", "interior": "...", "disposables": "...", "eliquids": "..." }
}
```
2. `python tools/rebrand.py new-brand.json`. It prints every swap, refuses to finish if anything of the old brand is left, and saves the new `brand.json`.

### What the fields do
- **phone / whatsapp**: the same number, written two ways (`+27 82 111 2222` and `27821112222`).
- **centre / road**: the mall or centre name and the road it's on. If there's no centre, use the suburb.
- **partnerName**: a delivery partner such as 7Waves. Set it to `""` and every partner card, button and sentence disappears, and "Three ways" becomes "Two ways".
- **onlineStore**: the shop's WooCommerce site. Leave it as `""` until the shop's own products are loaded; the "Buy now" checkout button stays hidden until then.
- **accent**: the brand's main colour. Every red tone in the theme moves to this hue (buttons, glows, tinted panels). WhatsApp green, Instagram colours and stars stay as they are.
- **images**: any picture format. The logo keeps transparency. Photos are centre-cropped to fit the layout.

## Products
- `assets/products.json` and `assets/details/` hold Cloudside's in-stock catalogue (2,277 items). A new shop can launch on these as sample stock.
- Shop on WooCommerce: change the address in `tools/snapshot.py` (the rebrand script does this when `domain` changes), then run `python tools/snapshot.py`. It keeps only in-stock items, fixes junk specs and silly prices, and rebuilds the catalogue.
- Not on WooCommerce: build a small importer that writes the same JSON shape (see the fields `snapshot.py` writes).
- Product photos load from Cloudside's server until a shop's own catalogue is loaded.

## Vape-specific features
- **Coil & Pod Finder**: `assets/fits.js`, one line per device family, matched by product name. Check it against the new shop's stock.
- **Nicotine pouch strength picker**: `POUCH_TIERS` in `assets/site.js` (3mg / 6mg / 10mg). The can's own strength shows as "In stock".
- **Vape finder quiz**: on the home page; uses the `FLAVOURS` patterns in `assets/site.js`.

## Test locally
`python -m http.server 5178`, then open http://localhost:5178. Check every page at phone width (375px) for sideways scrolling and console errors.

## Publish (GitHub Pages)
GitHub CLI: `C:\Users\HP\tools\gh\bin\gh.exe`.
`git init`, commit, then `gh repo create <name> --public --source=. --push`, then `gh api -X POST repos/<user>/<name>/pages -f "source[branch]=main" -f "source[path]=/"`.
Every page has `<meta name="robots" content="noindex, nofollow">` so demos stay out of Google. Remove it once the owner signs off.

## Not included in this folder
`report/` holds the Cloudside sales proposal (PDF and screenshots). It's Cloudside-only; delete it in a client copy.
