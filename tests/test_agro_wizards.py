# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestAgroSaleWizard(TransactionCase):
    """Tests for agro.sale.wizard — covers confirm flow and validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Storable product with lot tracking — required for picking + lot assignment
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Seeds',
            'type': 'product',
            'tracking': 'lot',
            'is_sellable': True,
            'list_price': 100.0,
        })
        cls.product = cls.product_tmpl.product_variant_ids[:1]

        # Customer and supplier partners
        cls.customer = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.supplier = cls.env['res.partner'].create({'name': 'Test Supplier'})

        # Stock location for on-hand quantity
        cls.stock_location = cls.env.ref('stock.stock_location_stock')

        # Batch with stock
        cls.lot = cls.env['stock.lot'].create({
            'name': 'BATCH/TEST/0001',
            'product_id': cls.product.id,
            'company_id': cls.env.company.id,
        })
        # Seed on-hand stock directly via quant
        cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.stock_location.id,
            'lot_id': cls.lot.id,
            'quantity': 50.0,
        })

    def test_sale_wizard_empty_lines_raises(self):
        """Wizard with no items must raise UserError — not silently create an empty order."""
        wizard = self.env['agro.sale.wizard'].create({
            'customer_id': self.customer.id,
            'payment_method': 'cash',
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_sale_wizard_creates_sale_order(self):
        """Confirm creates a sale.order flagged as shop sale with correct total."""
        wizard = self.env['agro.sale.wizard'].create({
            'customer_id': self.customer.id,
            'payment_method': 'upi',
            'line_ids': [(0, 0, {
                'product_id': self.product_tmpl.id,
                'lot_id': self.lot.id,
                'quantity': 2.0,
                'unit_price': 100.0,
                'discount_pct': 0.0,
            })],
        })
        wizard.action_confirm()

        sale = self.env['sale.order'].search([
            ('partner_id', '=', self.customer.id),
            ('agro_is_shop_sale', '=', True),
        ], limit=1)

        self.assertTrue(sale, 'sale.order not created')
        self.assertEqual(sale.agro_payment_method, 'upi')
        self.assertAlmostEqual(sale.amount_total, 200.0)

    def test_sale_wizard_discount_applied(self):
        """50% discount on a 100.0 line → subtotal 50.0 → order total 50.0."""
        wizard = self.env['agro.sale.wizard'].create({
            'customer_id': self.customer.id,
            'payment_method': 'cash',
            'line_ids': [(0, 0, {
                'product_id': self.product_tmpl.id,
                'lot_id': self.lot.id,
                'quantity': 1.0,
                'unit_price': 100.0,
                'discount_pct': 50.0,
            })],
        })
        wizard.action_confirm()

        sale = self.env['sale.order'].search([
            ('partner_id', '=', self.customer.id),
            ('agro_is_shop_sale', '=', True),
        ], order='id desc', limit=1)

        self.assertAlmostEqual(sale.amount_total, 50.0)

    def test_sale_wizard_default_customer_from_config(self):
        """Walk-in customer from config must be pre-filled on new wizard."""
        walkin = self.env['res.partner'].create({'name': 'Walk-in Test'})
        config = self.env['inventory.config'].get_config()
        config.default_walkin_partner_id = walkin

        wizard = self.env['agro.sale.wizard'].new({})
        defaults = wizard.default_get(['customer_id'])
        self.assertEqual(defaults.get('customer_id'), walkin.id)


@tagged('post_install', '-at_install')
class TestAgroPurchaseWizard(TransactionCase):
    """Tests for agro.purchase.wizard — covers receive flow and validation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Fertilizer',
            'type': 'product',
            'tracking': 'lot',
            'is_purchasable': True,
        })
        cls.product = cls.product_tmpl.product_variant_ids[:1]
        cls.supplier = cls.env['res.partner'].create({'name': 'Test Supplier'})

    def test_purchase_wizard_empty_lines_raises(self):
        """Wizard with no items must raise UserError."""
        wizard = self.env['agro.purchase.wizard'].create({
            'supplier_id': self.supplier.id,
        })
        with self.assertRaises(UserError):
            wizard.action_receive()

    def test_purchase_wizard_creates_purchase_order(self):
        """Confirm creates a purchase.order with correct supplier and total."""
        wizard = self.env['agro.purchase.wizard'].create({
            'supplier_id': self.supplier.id,
            'line_ids': [(0, 0, {
                'product_id': self.product_tmpl.id,
                'quantity': 10.0,
                'unit_price': 25.0,
                'batch_name': 'BATCH/TEST/PO001',
            })],
        })
        wizard.action_receive()

        po = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ], order='id desc', limit=1)

        self.assertTrue(po, 'purchase.order not created')
        self.assertAlmostEqual(po.amount_total, 250.0)

    def test_purchase_wizard_creates_stock_lot(self):
        """Each received line must create a stock.lot with the correct batch name."""
        batch_name = 'BATCH/TEST/LOT999'
        wizard = self.env['agro.purchase.wizard'].create({
            'supplier_id': self.supplier.id,
            'line_ids': [(0, 0, {
                'product_id': self.product_tmpl.id,
                'quantity': 5.0,
                'unit_price': 10.0,
                'batch_name': batch_name,
            })],
        })
        wizard.action_receive()

        lot = self.env['stock.lot'].search([
            ('name', '=', batch_name),
            ('product_id', '=', self.product.id),
        ], limit=1)

        self.assertTrue(lot, 'stock.lot not created for received batch')

    def test_purchase_wizard_stock_increases(self):
        """After receiving, on-hand qty for the product must increase."""
        qty_before = self.product.qty_available

        wizard = self.env['agro.purchase.wizard'].create({
            'supplier_id': self.supplier.id,
            'line_ids': [(0, 0, {
                'product_id': self.product_tmpl.id,
                'quantity': 20.0,
                'unit_price': 10.0,
                'batch_name': 'BATCH/TEST/QTY001',
            })],
        })
        wizard.action_receive()

        # Invalidate cache so qty_available is re-read from DB
        self.product.invalidate_recordset()
        qty_after = self.product.qty_available

        self.assertGreater(qty_after, qty_before, 'Stock did not increase after receive')
