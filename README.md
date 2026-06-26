# Agro & Seeds Shop — Inventory Management

A custom Odoo 16 module built for a single-operator agro and seeds retail shop. Simplifies daily stock management, sales, purchasing, batch tracking, and customer credit/village/crop tracking without requiring the operator to navigate complex Odoo workflows.

> Looking for the plain-language operator manual? See [`USER_GUIDE.md`](USER_GUIDE.md). This file is the technical/developer reference.

---

## What It Does

| Feature | Description |
|---|---|
| **Quick Sale** | One-screen wizard to create a confirmed sale order, assign batch, deduct stock, and print a receipt — in one click |
| **Quick Purchase / Receive Stock** | One-screen wizard to create a purchase order, generate a batch number, and update on-hand stock |
| **Batch Tracking** | Every product purchase creates a `stock.lot` with batch number, expiry date, and cost price |
| **Expiry Alerts** | Batches approaching or past expiry are flagged in a dedicated list view |
| **FIFO Auto-Selection** | Sale wizard automatically pre-selects the oldest in-date batch per product |
| **Stock Overview** | Read-only view showing all products with live stock levels and ok/low/out status |
| **Sales & Purchase History** | Filtered views of all past shop orders linked back to Odoo standard models |
| **PDF Receipt** | Printable receipt with shop header (name, logo, address, GST), line items, batch numbers, discounts, due date for credit sales, and configurable footer |
| **Shop Config** | Singleton configuration record for shop name, logo, address, phone, GST number, expiry warning threshold, and default walk-in customer |
| **Customer Profiles** | Village, crops grown, per-customer credit period, and a field-notes log on every contact |
| **Billing Ledger** | Cash/UPI/Other settle instantly; Credit sales carry a balance with a due date — no accounting module required |
| **Receive Payment (FIFO)** | One button on the customer form; payment auto-applies to their oldest unpaid bill first, spilling into the next if it overpays |
| **Risk Classification** | Green/Yellow/Red badge per customer, recomputed live and by a nightly cron, based on overdue bills |
| **Overdue Bills** | One menu showing every unpaid bill currently past its due date, oldest/worst first |
| **Top Customers** | One sortable, groupable list of every customer — purchase total, outstanding balance, risk, village — instead of separate reports |

---

## Module Structure

```
inventory_management/
├── __init__.py
├── __manifest__.py
├── controllers/
│   └── controllers.py              # Placeholder — no HTTP routes yet
├── data/
│   ├── default_data.xml            # Seed data: walk-in partner, categories, UoM records, shop config
│   ├── sequence_data.xml           # Batch number sequence (BATCH/YYYYMMDD/XXXX)
│   ├── uom_data.xml                # Custom UoM setup (nos/pack/bag/bundle, archives unused units)
│   ├── agro_crop_data.xml          # Seed crop list (10 crops)
│   └── agro_cron_data.xml          # Nightly job: re-flag bills that crossed their due date
├── demo/
│   └── demo.xml                    # Demo data for Odoo demo mode
├── models/
│   ├── __init__.py
│   ├── inventory_category.py       # Shop-specific product categories
│   ├── inventory_config.py         # Singleton shop configuration
│   ├── product_template_ext.py     # Extends product: category, min stock, stock status
│   ├── stock_lot_ext.py            # Extends stock.lot: expiry status, cost price, batch sequence
│   ├── uom_ext.py                  # One-time setup: rename/archive UoMs to the agreed minimal set
│   ├── sale_order_ext.py           # Extends sale.order: payment method, shop sale flag, credit ledger
│   ├── agro_sale_wizard.py         # TransientModel — Quick Sale form + action_confirm
│   ├── agro_purchase_wizard.py     # TransientModel — Receive Stock form + action_receive
│   ├── agro_village.py             # Customer village master data
│   ├── agro_crop.py                # Crop master data
│   ├── agro_customer_note.py       # Field notes logged against a customer
│   ├── agro_customer_payment.py    # Payment + FIFO allocation ledger
│   └── res_partner_ext.py          # Village/crops/credit period/notes/payments/risk on the contact
├── reports/
│   ├── sale_receipt_report.xml     # Report action definition
│   └── sale_receipt_template.xml   # QWeb PDF receipt template (shows due date for credit sales)
├── security/
│   ├── agro_security.xml           # group_agro_cashier / group_agro_manager
│   └── ir.model.access.csv         # Access control for all custom models
├── tests/
│   ├── __init__.py
│   ├── test_agro_wizards.py        # 8 tests: sale + purchase wizard flows
│   └── test_agro_credit_ledger.py  # 23 tests: ledger, FIFO, risk, cron, line constraints
└── views/
    ├── agro_purchase_wizard_views.xml
    ├── agro_sale_wizard_views.xml
    ├── agro_village_views.xml
    ├── agro_crop_views.xml
    ├── agro_customer_note_views.xml
    ├── agro_customer_payment_views.xml
    ├── res_partner_views.xml
    ├── res_partner_top_customers_views.xml
    ├── sale_order_overdue_views.xml
    ├── inventory_category_views.xml
    ├── inventory_config_views.xml
    ├── menus.xml
    ├── product_views.xml
    ├── purchase_history_views.xml
    ├── sale_history_views.xml
    ├── stock_lot_views.xml
    └── stock_overview_views.xml
```

---

## Dependencies

| Odoo Module | Reason |
|---|---|
| `uom` | Native unit of measure framework — used directly on `product.template.uom_id` |
| `product` | `product.template` and `product.product` |
| `stock` | `stock.lot`, `stock.quant`, `stock.picking`, `stock.move` |
| `sale` | `sale.order`, `sale.order.line` |
| `purchase` | `purchase.order`, `purchase.order.line` |
| `mail` | Chatter on Odoo standard models |
| `product_expiry` | Expiry date tracking on batches |

> `res.partner.currency_id` (used by the billing ledger's Monetary fields) is provided by the `account` module — a transitive dependency via `sale` → `account_payment` → `account`. Not declared directly since it's always present once `sale` is installed.

---

## Installation

### Requirements

- Odoo **16.0**
- Python 3.10+
- PostgreSQL 14+

### Steps

1. Copy the `inventory_management` folder into your Odoo `addons` or custom addons path.
2. Restart the Odoo server.
3. Go to **Settings → Apps**, search for `Agro & Seeds Shop`, and click **Install**.
4. Set the company currency (Settings → General Settings → Currency) to whatever the shop actually trades in — a fresh Odoo install defaults to EUR.

### Upgrading after a code change

A plain service restart only re-imports the Python source — it does **not** create new database columns/tables for changed models. After editing any model, run a real upgrade:

```
net stop <your-odoo-service>
"<path-to-python>\python.exe" "<path-to-odoo-bin>" -c "<path-to-odoo.conf>" -d <your_db> -u inventory_management --stop-after-init
net start <your-odoo-service>
```

On at least one observed Windows install, the Apps page's "Upgrade" button did **not** reliably apply schema changes (no errors logged, but new columns never appeared) — the CLI command above is the verified-reliable method. Confirm success by checking the schema directly (`\d sale_order`, `\dt agro_*` in psql) rather than trusting "no errors in the log" alone.

---

## Configuration

After installation, go to **Agro Inventory → Configuration → Shop Settings** and fill in:

| Field | Description |
|---|---|
| Shop Name | Printed on receipts |
| Address | Printed on receipts |
| Phone | Printed on receipts |
| Logo | Printed on receipts (binary upload) |
| GST Number | Printed on receipts if filled |
| Receipt Footer | Custom message at bottom of receipt |
| Expiry Warning (days) | Days before expiry to flag batches as "Expiring Soon" (default: 30) |
| Default Credit Period (days) | Default number of days a new customer gets before a credit bill is overdue (default: 30) — editable per customer afterward |
| Walk-in Customer | Partner auto-filled on every new sale — no need to select for cash walk-ins |

Restricted to the **Manager** group (see [Security Groups](#security-groups)) — cashiers can view but not change shop settings.

---

## Daily Usage

See [`USER_GUIDE.md`](USER_GUIDE.md) for the full plain-language walkthrough. Quick reference:

### Making a Sale
1. **Agro Inventory → New Sale**
2. Customer is pre-filled (walk-in customer from config)
3. Add items — batch is auto-selected (FIFO: oldest in-date batch first)
4. Set payment method (Cash / UPI / Credit / Other) — Cash/UPI/Other settle instantly, Credit carries a balance
5. Click **Confirm & Print Receipt** — stock is deducted, receipt opens as PDF (shows the due date if Credit)

### Receiving Stock
1. **Agro Inventory → Receive Stock**
2. Select supplier
3. Add items — batch number is auto-generated, enter cost price and expiry date
4. Click **Receive** — stock is added, a new batch is created

### Receiving a Payment
1. Open the customer's contact record
2. Click **Receive Payment**, enter the amount, save
3. It's automatically applied to their oldest unpaid bill(s) first (FIFO), with any leftover spilling into the next-oldest

### Checking Who Owes Money
- **Agro Inventory → Overdue Bills** — every unpaid bill currently past its due date
- **Agro Inventory → Top Customers** — every customer, sortable by any column, groupable by Village or Risk

---

## Data Models

### Custom Models

| Model | Description |
|---|---|
| `inventory.category` | Shop-specific product category (Seeds, Fertilizers, etc.) |
| `inventory.config` | Singleton shop configuration (name, logo, GST, expiry threshold, default credit period) |
| `agro.sale.wizard` / `.line` | Transient: quick sale form — creates `sale.order` on confirm |
| `agro.purchase.wizard` / `.line` | Transient: quick purchase form — creates `purchase.order` on receive |
| `agro.village` | Village master data, linked from `res.partner` |
| `agro.crop` | Crop master data, many2many on `res.partner` (10 seeded on install) |
| `agro.customer.note` | Free-text field-history note logged against a customer, dated and attributed |
| `agro.customer.payment` | A payment received from a customer — auto-allocates itself via FIFO on create |
| `agro.customer.payment.allocation` | One slice of a payment applied to one bill — the audit trail behind the FIFO split |

### Extended Odoo Models

| Model | Extended With |
|---|---|
| `product.template` | `agro_category_id`, `min_stock`, `stock_status` (computed) |
| `stock.lot` | `purchase_date`, `unit_price`, `days_to_expiry`, `expiry_status` (computed), auto batch sequence |
| `sale.order` | `agro_payment_method`, `agro_is_shop_sale`, `agro_amount_paid`, `agro_amount_outstanding`, `agro_due_date`, `agro_is_overdue`, `agro_days_overdue`, `agro_products_summary` |
| `sale.order.line` | `agro_lot_id` (batch sold per line), `agro_sold_qty`, `agro_sold_uom_id` |
| `res.partner` | `village_id`, `crop_ids`, `credit_period`, `note_ids`, `payment_ids`, `agro_payment_count`, `agro_total_outstanding`, `agro_total_purchased`, `risk_classification` |

---

## Billing Ledger — Design Decision

Credit/overdue/payment tracking uses a **lightweight custom ledger directly on `sale.order`** ("the bill") — deliberately **not** Odoo's native accounting (`account.move`/Invoicing). This was an explicit choice: it avoids exposing Chart of Accounts, Journals, and Taxes to a non-technical, single-operator shop owner, and keeps the existing Quick Sale wizard flow completely unchanged.

How it works:
- `agro_payment_method != 'credit'` (i.e. Cash/UPI/Other) → `action_confirm()` immediately sets `agro_amount_paid = amount_total`. Settled at the counter, no balance carried.
- `agro_payment_method == 'credit'` → stays unpaid until a `agro.customer.payment` is recorded against the customer.
- `agro_due_date = date_order + partner.credit_period` (days), recomputed automatically if either changes.
- `agro_is_overdue` / `agro_days_overdue` depend on "today", which doesn't fire Odoo's own change-tracking on its own — a nightly `ir.cron` (`data/agro_cron_data.xml`) force-recomputes them once a day so a bill that quietly crosses its due date overnight gets flagged without anyone touching it.
- `res.partner.risk_classification`: **red** = any bill over 60 days overdue, or 2+ bills currently overdue; **yellow** = exactly 1 bill overdue (≤60 days); **green** = none. These exact thresholds are an assumption, not yet confirmed by the client — see Known Limitations.
- Payments (`agro.customer.payment`) apply themselves via FIFO on `create()` — oldest unpaid bill first, with the remainder spilling into the next-oldest. Deleting a payment reverses its effect on every bill it touched. Editing the `amount` or `partner_id` of an already-applied payment is blocked (delete + re-create instead) to avoid silently corrupting the ledger.

**Known gotcha discovered during testing:** Odoo's own `sale.order.action_confirm()` always resets `date_order` to `now()` regardless of what was set at creation (`_prepare_confirmation_values`). `SaleOrderExt.action_confirm()` captures and restores the chosen date for shop sales specifically, so a backdated entry (e.g. logging yesterday's sale today) actually sticks.

---

## Security Groups

| Group | Access |
|---|---|
| `group_agro_cashier` | Day-to-day selling/receiving. Read-only on Shop Settings. |
| `group_agro_manager` | Everything Cashier can do, plus full read/write/create/delete on Shop Settings. Implies Cashier. The default Administrator user is assigned this group on install. |

All other custom models (villages, crops, notes, payments, wizards) currently grant full access to any internal user (`base.group_user`) — appropriate for a one-person shop; tighten further if staff accounts are ever added.

---

## Unit of Measure

This module uses **Odoo's native `uom.uom`** framework (`product.template.uom_id` and `uom_po_id`) directly.

On install, `uom_ext.py`'s `_setup_agro_uoms()` renames the standard Unit/kg/g/Litre UoMs to lowercase (unit/kgs/gm/ltr), creates a `nos` unit, and **archives every other UoM** except the agreed minimal set (unit, nos, kgs, gm, ltr, ml, pack, bag, bundle) — this keeps the dropdown short for a non-technical operator. If a product elsewhere in the database already uses a UoM outside that list, archiving it will affect that product too; this was an accepted tradeoff for this single-purpose install, not something to reuse on a shared/multi-purpose database.

> This ensures full compatibility with Odoo Website, POS, and accounting modules if added in future.

---

## Batch Numbering

Auto-generated batch numbers follow this format:

```
BATCH/YYYYMMDD/XXXX
Example: BATCH/20260604/0001
```

Generated by Odoo's `ir.sequence` (`agro.batch`). Operators can override manually at receive time.

---

## Receipt Template

The PDF receipt includes:

- Shop header: name, logo, address, phone, GST
- Receipt number, date, payment method
- **Amount Due and due date**, shown only for Credit sales
- Customer name and serving operator
- Line items: product, batch, quantity, price, discount %, subtotal
- Grand total
- Order notes
- Configurable footer from shop config

---

## Tests

Tests use Odoo's `TransactionCase` (each test runs in its own savepoint, rolled back automatically — safe to run against a real database).

Run with:

```bash
./odoo-bin -u inventory_management --test-enable --stop-after-init -d <your_db>
```

Check the result with `grep "odoo.tests.result" odoo.log` — look for `0 failed, 0 error(s)`.

### `test_agro_wizards.py` (8 tests)

| Test | Covers |
|---|---|
| `test_sale_wizard_empty_lines_raises` | `UserError` raised when no items added |
| `test_sale_wizard_creates_sale_order` | Sale order created with correct payment method and total |
| `test_sale_wizard_discount_applied` | 50% discount correctly reduces subtotal |
| `test_sale_wizard_default_customer_from_config` | Walk-in customer pre-filled from shop config |
| `test_purchase_wizard_empty_lines_raises` | `UserError` raised when no items added |
| `test_purchase_wizard_creates_purchase_order` | Purchase order created, validated, total correct |
| `test_purchase_wizard_creates_stock_lot` | `stock.lot` created with correct batch name |
| `test_purchase_wizard_stock_increases` | On-hand quantity increases after receive |

### `test_agro_credit_ledger.py` (23 tests)

| Test | Covers |
|---|---|
| `test_credit_sale_leaves_outstanding_with_due_date` | Credit sale stays unpaid with correct due date |
| `test_cash_sale_auto_settles` / `test_upi_sale_auto_settles` | Cash/UPI settle instantly |
| `test_payment_fifo_pays_oldest_first_with_spillover` | Payment splits correctly across 2 bills |
| `test_payment_delete_reverses_allocation` | Deleting a payment restores the balance |
| `test_payment_amount_locked_after_allocation` | Editing an applied payment's amount is blocked |
| `test_risk_classification_thresholds` | Green → Yellow (≤60d) → Red (>60d) |
| `test_risk_classification_red_on_two_overdue_bills` | 2+ overdue bills → Red, even if each is under 60 days |
| `test_date_order_survives_confirmation` | Regression test: confirming a shop sale no longer resets its date |
| `test_cron_recomputes_overdue_orders` | Cron computes the right overdue status for both stale and fresh orders |
| `test_sale_line_rejects_*` / `test_purchase_line_rejects_*` (5 tests) | Qty/price/discount validation on both wizards |

---

## Known Limitations

| Issue | Status |
|---|---|
| Exact risk thresholds (red/yellow/green) | Assumption, not yet confirmed by the actual client |
| Crop-quantity-per-history display | Not yet asked/confirmed whether quantity matters, only which crops |
| Order cancellation / returns | Not supported — the ledger fields don't account for a cancelled or returned order |
| Concurrent payment registration | `agro.customer.payment`'s FIFO allocation has no locking; a true risk only if multiple staff register payments for the same customer at the exact same moment |
| `agro_payment_method = 'other'` | Currently auto-settles like Cash/UPI — this was an assumption, not confirmed with the client |
| No CI pipeline | Tests must be run manually against a live Odoo database |
| No online sales / API layer | HTTP controllers are placeholder only |
| Pre-existing filestore corruption | A small number of `ir.attachment` rows reference files missing from disk on at least one observed install — unrelated to this module's code, not cleaned up |

---

## Architecture Notes

- All permanent data lives in standard Odoo models (`sale.order`, `purchase.order`, `stock.lot`, `res.partner`). Wizards are `TransientModel` — UI only.
- `read_group` used for all computed count fields — no N+1 queries.
- `inventory.unit` custom model was removed in favour of native `uom.uom` — avoids ecosystem conflicts.
- Module follows Odoo MVC conventions: models in `models/`, views in `views/`, access rules in `security/`.
- UI principle followed throughout: the shop owner is a single, non-technical operator — every feature prefers adding a button/field to a screen that already exists over creating a new menu. Only two new top-level menus exist for the entire credit/village/crop feature set: **Overdue Bills** and **Top Customers**.

---

## Odoo Version

**Odoo 16.0 Community**

---

## License

Proprietary. For internal use only.
