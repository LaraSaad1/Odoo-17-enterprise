# Spark Chemicals — Quotation Offer Report (Odoo 17)

Custom module that reproduces the "عرض سعر" (Price Offer) PDF, printed straight from
the **Product** list/tree view or the **Product** form view — no Sale Order needed,
and just **one** wizard (no nested popups).

## How it works

1. Go to **Sales → Products → Products** (or wherever `product.template` is listed).
2. **From the list/tree view**: tick one or more products (checkboxes) →
   ⚙ **Actions** menu → **"طباعة عرض سعر"**.
   **From the form view**: open a single product → click the **"طباعة عرض سعر"**
   button at the top (or the same ⚙ Actions menu entry).
3. A single wizard opens with one row already filled in per product you had
   selected/open — **nothing to pick manually there**. Fill in **مرسل إليه**
   (consignee/recipient — the only field you type by hand) and, for each line,
   optionally adjust **الوحدة** (the unit/weight variant to print).
4. Click **"طباعة عرض السعر"** → the PDF downloads.

### Why this is now reliable (no more "wizard inside a wizard")

Earlier versions relied on `default_get()` guessing the product from
`active_id`/`active_model` context, and displayed the product as an editable
Many2one cell. Two things could go wrong with that: the context guess could
silently fail (empty wizard), and clicking an empty/readonly Many2one cell in a
list makes Odoo fall back to opening a full **create-record popup** for that
related model — which is the nested dialog you ran into.

This version fixes both, on `models/product_template.py`:
- `action_open_quotation_offer_wizard()` runs **server-side**, builds the wizard's
  lines explicitly from `self` (the record(s) you're on/selected), and opens the
  wizard via the standard `default_line_ids` context key — no guessing.
- The product column in the wizard is now a **plain read-only text field**
  (`product_name`, a `related` Char), not a clickable relational widget, so there
  is no path left for it to ever open a nested popup.
- The list no longer allows adding new lines (`create="false"`), so there's no way
  to end up with a blank, unfillable row either.

## What's on the report

1. **Automatic unit price** — `سعر الوحده` is computed live from the pricelist named
   **`قطاع مزارع`** (see `FARM_PRICELIST_NAME` in
   `wizard/quotation_offer_wizard.py` if you ever rename it), resolved against the
   specific variant matching the `الوحدة` you picked (falls back to the product's
   default variant, then to its sales price, if no pricelist/variant match is found).
2. **Formulation / Pests / Crop pulled automatically, nothing to type** — the report
   reads directly from your **existing** `product.template` fields `formulation`,
   `pests` and `crop`. This module does not define or touch those fields — it only
   reads them.
3. **Dynamic columns** — each optional column (`الآفه`, `اسم الماده الفعاله`,
   `المحصول`, `الوحده`, `سعر الوحده`) only prints if **at least one** line actually
   has a value for it. `م` and `اسم الصنف` always show.
4. **Different labels than technical names** — see the mapping table below.

## Field mapping (as requested)

| Technical name | Model | Report label | Source |
|---|---|---|---|
| `price_unit` (computed, wizard line) | `quotation.offer.wizard.line` | سعر الوحده | Computed from pricelist `قطاع مزارع` against the chosen variant |
| `attribute_value_id` → `.name` | `product.template.attribute.value` | الوحده | Chosen by the user in the wizard, scoped to that product |
| `formulation` | `product.template` (existing field) | الماده الفعاله | Read-only, already on the product |
| `pests` | `product.template` (existing field) | الآفه | Read-only, already on the product |
| `crop` | `product.template` (existing field) | المحصول | Read-only, already on the product |
| `name` | `product.template` | اسم الصنف | Product name |
| `consignee_name` | `quotation.offer.wizard` | مرسل إليه | Typed by the user in the wizard |

## Install / upgrade

1. Copy the `custom_quotation_offer` folder into your Odoo 17 `addons` path
   (overwrite the previous version if you had it installed).
2. Restart the Odoo server.
3. **Apps → Update Apps List**, then find "Spark Chemicals - Quotation Offer Report"
   and click **Upgrade** (not just Install, if it was already installed).
4. Make sure a pricelist literally named **`قطاع مزارع`** exists
   (Sales → Configuration → Pricelists, or Inventory → Configuration → Pricelists
   depending on your app setup). If it can't be found, the wizard falls back to the
   variant's own list price so the report never breaks.
5. Go to **Settings → General Settings → Companies** and set your company **logo**
   (Spark logo) — the report uses it automatically, with a text fallback if unset.
6. Make sure the products you offer already have `formulation`, `pests` and `crop`
   filled in wherever your existing UI exposes them, and that their attribute values
   (e.g. "Weight") are created under **Attributes & Variants**, so they're
   selectable as `الوحدة` in the wizard.

## Why the PDF was garbled (Arabic showing as `Ø§Ù...`)

This is a known Odoo/wkhtmltopdf bug ([odoo/odoo#80184](https://github.com/odoo/odoo/issues/80184)):
with **wkhtmltopdf 0.12.6**, Odoo doesn't pass an explicit `--encoding utf-8` flag
to the renderer, so on some platforms (notably Windows) it falls back to reading
the UTF-8 HTML as Windows-1252/Latin-1. Every 2-byte Arabic (or accented) character
then turns into 2 garbled Latin letters — exactly the `Ø§Ù...` pattern you saw.

This module now fixes it at the source: `models/ir_actions_report.py` inherits
`ir.actions.report` and appends `--encoding utf-8` to the wkhtmltopdf command
arguments for **all** PDF reports on your system (not just this one) if it isn't
already present. No need to touch your wkhtmltopdf installation. If you'd rather
fix it system-wide instead, downgrading to wkhtmltopdf **0.12.5** (with patched Qt)
also resolves it, per Odoo's official recommendation.

## Notes / things you may want to tweak

- The report title bar color (`#2aa7a0`) is a close approximation of the Spark teal —
  adjust the hex codes in `report/quotation_offer_report_template.xml` to match your
  exact brand color if needed.
- The footer address block pulls `company.street`, `company.phone`, `company.email`,
  `company.website` from **Settings → Companies**. Fill those in so the footer
  matches the sample PDF exactly.
- If a product has multiple variants and you don't pick a `الوحدة` for it, the price
  falls back to that product's *default* variant's price — pick a value if the
  product's variants have different prices.
