# Telesales — Odoo 17 module

Tracks telesales calls (farmers / traders / companies) with fields and
labels matching your sheet, and adds an English "Telesales" sub-menu
under CRM > Salesperson Planner (`crm_salesperson_planner.menu_salesperson_planner`),
next to "My Visits" / "All Visits" / "Visit Templates":
**Telesales > Calls / Customers**. "Calls" opens with a "My Calls" filter
applied by default (clear it in the search bar to see everyone's calls).

## Field mapping (sheet -> Odoo field)

| Sheet column (Arabic)             | Odoo field       | Type / label |
|------------------------------------|------------------|--------------|
| اليوم                              | `day_of_week`    | Selection, regular editable field — auto-filled from `call_date` on change/default, freely overridable |
| التاريخ                            | `call_date`      | Date — defaults to today, fully editable |
| اسم العميل                         | `customer_id`    | Many2one -> new **Telesales Customer** model (`telesales.customer`), with the usual Odoo "Create '...'" / "Create and edit..." options right on the field |
| التليفون                           | `phone`          | Char, label "التليفون" (auto-filled from the selected customer, still editable per call) |
| ملاحظات (1st)                      | `notes`          | Text, label "ملاحظات" |
| المحافظه                           | `governorate_id` | Many2one **res.country.state**, domain limited to Egypt. Uses whatever data/labels already exist in your database — this module does not modify res.country.state in any way |
| المركز                             | `center`         | Char, label "المركز" |
| مزارع - تجاري - عربيات             | `category`       | Selection: مزارع / تجاري / عربيات |
| اسم المنتج                         | `product_id`     | Many2one product.product |
| اسم الموظف                         | `employee_id`    | Many2one res.users |
| ملاحظات (2nd, employee outcome)    | `employee_notes` | Text, label "ملاحظات الموظف" |
| —                                   | `state`          | جديد / مؤكد / ملغي workflow |

Field labels, group headers, buttons, and filters inside the forms stay in
Arabic (matching your sheet). The Telesales sub-menu items themselves
(Calls, Customers) are in English.

## Telesales Customer (`telesales.customer`)

A small customer master-data model: name (اسم العميل, required), phone,
governorate, center, category, notes. `اسم العميل` on a call is a
dropdown against this model — type a new name and Odoo offers
"Create '...'" (quick) or "Create and edit..." (full form) right there,
no need to leave the call form. Picking an existing customer auto-fills
phone/governorate/center/category on the call (still editable per call).
Manage the full list from Telesales > Customers.

## Governorates (res.country.state)

`governorate_id` just points at Odoo's standard `res.country.state`
model, filtered to Egypt. It's shown as a normal field on the call and
customer forms only — there's no separate Telesales menu for it, and the
module doesn't seed, rename, or translate anything on
`res.country.state`; it uses whatever's already in your database.

## Install

1. Copy the `telesales` folder into your Odoo 17 `addons` path.
2. Restart the Odoo service.
3. Apps > Update Apps List.
4. Search "Telesales" and click Install.

Depends on `crm`, `sale`, `product`, and `crm_salesperson_planner` (the
module providing your Salesperson Planner menu).

## Importing your existing sheet data

Go to Telesales > Calls, clear the "My Calls" filter if you want to see
everything, then use the list view's Import and map columns to: `call_date`, `customer_id/name` (matches/creates a Telesales
Customer), `phone`, `notes`, `governorate_id/name`, `center`, `category`
(`farmer` / `commercial` / `car`), `employee_id/name`, `employee_notes`.
`day_of_week` doesn't need to be imported — it defaults from `call_date`
automatically, though you can still set it explicitly per row if needed.

If you'd rather bulk-load `telesales.customer` records first (deduplicated
by name/phone) and then import calls referencing them, that's also fine —
just import Customers before Calls.
