# Agro & Seeds Shop — Inventory Management

A custom Odoo 16 module built for a single-operator agro and seeds retail shop. Simplifies daily stock management, sales, purchasing, and batch tracking without requiring the operator to navigate complex Odoo workflows.

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
| **PDF Receipt** | Printable receipt with shop header (name, logo, address, GST), line items, batch numbers, discounts, and configurable footer |
| **Shop Config** | Singleton configuration record for shop name, logo, address, phone, GST number, expiry warning threshold, and default walk-in customer |

---

## Module Structure

```
inventory_management/
├── __init__.py
├── __manifest__.py
├── controllers/
│   └── controllers.py          # Placeholder — no HTTP routes yet
├── data/
│   ├── default_data.xml        # Seed data: walk-in partner, categories, UoM records, shop config
│   └── sequence_data.xml       # Batch number sequence (BATCH/YYYYMMDD/XXXX)
├── demo/
│   └── demo.xml                # Demo data for Odoo demo mode
├── models/
│   ├── __init__.py
│   ├── inventory_category.py   # shop-specific product categories
│   ├── inventory_config.py     # Singleton shop configuration
│   ├── product_template_ext.py # Extends product: category, min stock, stock status
│   ├── sale_order_ext.py       # Extends sale.order: payment method, shop sale flag
│   ├── stock_lot_ext.py        # Extends stock.lot: expiry status, cost price, batch sequence
│   ├── agro_sale_wizard.py     # TransientModel — Quick Sale form + action_confirm
│   ├── agro_purchase_wizard.py # TransientModel — Receive Stock form + action_receive
│   └── models.py               # Reserved placeholder
├── reports/
│   ├── sale_receipt_report.xml    # Report action definition
│   └── sale_receipt_template.xml  # QWeb PDF receipt template
├── security/
│   └── ir.model.access.csv     # Access control for all custom models
├── tests/
│   ├── __init__.py
│   └── test_agro_wizards.py    # 8 test cases covering sale + purchase wizard flows
└── views/
    ├── agro_purchase_wizard_views.xml
    ├── agro_sale_wizard_views.xml
    ├── inventory_category_views.xml
    ├── inventory_config_views.xml
    ├── inventory_unit_views.xml   # Cleared — native uom.uom used instead
    ├── menus.xml
    ├── product_views.xml
    ├── purchase_history_views.xml
    ├── sale_history_views.xml
    ├── stock_lot_views.xml
    ├── stock_overview_views.xml
    ├── templates.xml
    └── views.xml
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
4. (Optional) Enable **Units of Measure** in Odoo settings to manage Pack, Bag, Bundle units.

---

## Configuration

After installation, go to **Agro Shop → Configuration → Shop Settings** and fill in:

| Field | Description |
|---|---|
| Shop Name | Printed on receipts |
| Address | Printed on receipts |
| Phone | Printed on receipts |
| Logo | Printed on receipts (binary upload) |
| GST Number | Printed on receipts if filled |
| Receipt Footer | Custom message at bottom of receipt |
| Expiry Warning (days) | Days before expiry to flag batches as "Expiring Soon" (default: 30) |
| Walk-in Customer | Partner auto-filled on every new sale — no need to select for cash walk-ins |

---

## Daily Usage

### Making a Sale

1. **Agro Shop → New Sale**
2. Customer is pre-filled (walk-in customer from config)
3. Add items — batch is auto-selected (FIFO: oldest in-date batch first)
4. Set payment method (Cash / UPI / Credit)
5. Click **Confirm & Print Receipt** — stock is deducted, receipt opens as PDF

### Receiving Stock

1. **Agro Shop → Receive Stock**
2. Select supplier
3. Add items — batch number is auto-generated, enter cost price and expiry date
4. Click **Receive** — stock is added, a new batch is created

---

## Data Models

### Custom Models

| Model | Description |
|---|---|
| `inventory.category` | Shop-specific product category (Seeds, Fertilizers, etc.) |
| `inventory.config` | Singleton shop configuration (name, logo, GST, expiry threshold) |
| `agro.sale.wizard` | Transient: quick sale form — creates `sale.order` on confirm |
| `agro.sale.wizard.line` | Transient: one item row in the sale wizard |
| `agro.purchase.wizard` | Transient: quick purchase form — creates `purchase.order` on receive |
| `agro.purchase.wizard.line` | Transient: one item row in the purchase wizard |

### Extended Odoo Models

| Model | Extended With |
|---|---|
| `product.template` | `agro_category_id`, `min_stock`, `stock_status` (computed) |
| `stock.lot` | `purchase_date`, `unit_price`, `days_to_expiry`, `expiry_status` (computed), auto batch sequence |
| `sale.order` | `agro_payment_method`, `agro_is_shop_sale` |
| `sale.order.line` | `agro_lot_id` (batch sold per line) |

---

## Unit of Measure

This module uses **Odoo's native `uom.uom`** framework (`product.template.uom_id` and `uom_po_id`) directly.

Three agro-specific units are seeded on install: **Pack**, **Bag**, **Bundle** — added under Odoo's standard "Unit" category.

Standard weight and volume units (kg, g, litre, ml) already exist in Odoo and are **not duplicated**.

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
- Customer name and serving operator
- Line items: product, batch, quantity, price, discount %, subtotal
- Grand total
- Order notes
- Configurable footer from shop config

---

## Tests

Tests are in `tests/test_agro_wizards.py` and use Odoo's `TransactionCase`.

Run with:

```bash
./odoo-bin -u inventory_management --test-enable --stop-after-init -d <your_db>
```

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

---

## Known Limitations

| Issue | Status |
|---|---|
| Access groups (Manager vs Cashier) | Not implemented — all authenticated users have full write access |
| Negative quantity/price validation | Not enforced in wizard — model constraints not yet added |
| Translation wrappers `_()` | UserError strings are not yet wrapped — untranslatable |
| No CI pipeline | Tests must be run manually against a live Odoo database |
| No online sales / API layer | HTTP controllers are placeholder only |

---

## Architecture Notes

- All permanent data lives in standard Odoo models (`sale.order`, `purchase.order`, `stock.lot`). Wizards are `TransientModel` — UI only.
- `read_group` used for all computed count fields — no N+1 queries.
- `inventory.unit` custom model was removed in favour of native `uom.uom` — avoids ecosystem conflicts.
- Module follows Odoo MVC conventions: models in `models/`, views in `views/`, access rules in `security/`.

---

## Odoo Version

**Odoo 16.0 Community**

---

## License

Proprietary. For internal use only.
