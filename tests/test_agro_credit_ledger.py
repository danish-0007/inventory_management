# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestAgroCreditLedger(TransactionCase):
    """Tests for the billing ledger: auto-settle, FIFO payment allocation, risk classification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Ledger Product',
            'type': 'consu',
            'is_sellable': True,
            'list_price': 100.0,
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Ledger Customer',
            'credit_period': 30,
        })

    def _make_order(self, payment_method, amount, days_ago=0):
        """Creates and confirms a bare shop sale.order for ledger testing (no wizard, no stock)."""
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'date_order': fields.Datetime.now() - timedelta(days=days_ago),
            'agro_payment_method': payment_method,
            'agro_is_shop_sale': True,
            'order_line': [(0, 0, {
                'product_id': self.product.product_variant_ids.id,
                'product_uom_qty': 1,
                'price_unit': amount,
            })],
        })
        order.action_confirm()
        return order

    def test_credit_sale_leaves_outstanding_with_due_date(self):
        order = self._make_order('credit', 1000.0)
        self.assertAlmostEqual(order.agro_amount_paid, 0.0)
        self.assertAlmostEqual(order.agro_amount_outstanding, 1000.0)
        self.assertEqual(order.agro_due_date, order.date_order.date() + timedelta(days=30))
        self.assertFalse(order.agro_is_overdue)

    def test_cash_sale_auto_settles(self):
        order = self._make_order('cash', 500.0)
        self.assertAlmostEqual(order.agro_amount_paid, 500.0)
        self.assertAlmostEqual(order.agro_amount_outstanding, 0.0)

    def test_upi_sale_auto_settles(self):
        order = self._make_order('upi', 250.0)
        self.assertAlmostEqual(order.agro_amount_paid, 250.0)
        self.assertAlmostEqual(order.agro_amount_outstanding, 0.0)

    def test_payment_fifo_pays_oldest_first_with_spillover(self):
        order_a = self._make_order('credit', 2000.0, days_ago=10)
        order_b = self._make_order('credit', 3000.0, days_ago=5)

        self.env['agro.customer.payment'].create({
            'partner_id': self.customer.id,
            'amount': 2500.0,
            'payment_method': 'cash',
        })

        self.assertAlmostEqual(order_a.agro_amount_outstanding, 0.0, msg='oldest bill should be fully paid first')
        self.assertAlmostEqual(order_b.agro_amount_outstanding, 2500.0, msg='remainder should spill into the next bill')

    def test_payment_delete_reverses_allocation(self):
        order = self._make_order('credit', 1000.0)
        payment = self.env['agro.customer.payment'].create({
            'partner_id': self.customer.id,
            'amount': 1000.0,
            'payment_method': 'cash',
        })
        self.assertAlmostEqual(order.agro_amount_outstanding, 0.0)

        payment.unlink()
        order.invalidate_recordset()
        self.assertAlmostEqual(order.agro_amount_outstanding, 1000.0, msg='deleting the payment should restore the balance')

    def test_payment_amount_locked_after_allocation(self):
        self._make_order('credit', 1000.0)
        payment = self.env['agro.customer.payment'].create({
            'partner_id': self.customer.id,
            'amount': 500.0,
            'payment_method': 'cash',
        })
        with self.assertRaises(UserError):
            payment.amount = 600.0

    def test_risk_classification_thresholds(self):
        order = self._make_order('credit', 1000.0)
        self.assertEqual(self.customer.risk_classification, 'green')

        # 1 bill, 45 days overdue -> yellow
        order.date_order = fields.Datetime.now() - timedelta(days=75)
        order._compute_agro_due_date()
        order._compute_agro_overdue()
        self.assertTrue(order.agro_is_overdue)
        self.assertEqual(self.customer.risk_classification, 'yellow')

        # push past 60 days overdue -> red
        order.date_order = fields.Datetime.now() - timedelta(days=100)
        order._compute_agro_due_date()
        order._compute_agro_overdue()
        self.assertGreater(order.agro_days_overdue, 60)
        self.assertEqual(self.customer.risk_classification, 'red')

    def test_date_order_survives_confirmation(self):
        # Odoo's own action_confirm() resets date_order to now() by default (_prepare_confirmation_values) —
        # our override must restore the operator's chosen date for shop sales afterward.
        order = self._make_order('credit', 1000.0, days_ago=40)
        self.assertEqual(order.date_order.date(), (fields.Datetime.now() - timedelta(days=40)).date())

    def test_risk_classification_red_on_two_overdue_bills(self):
        order_a = self._make_order('credit', 1000.0, days_ago=40)
        order_b = self._make_order('credit', 1000.0, days_ago=40)
        self.assertTrue(order_a.agro_is_overdue and order_b.agro_is_overdue)
        self.assertEqual(self.customer.risk_classification, 'red', msg='2+ overdue bills should be red even under 60 days each')

    def test_cron_recomputes_overdue_orders(self):
        # Real day-rollover staleness (a stored compute field going stale purely because "today"
        # advanced, with no write to trigger Odoo's own dependency tracking) can't be faked inside
        # a single rolled-back transaction — any cache invalidation on a stored computed field makes
        # Odoo recompute it fresh on next read, which self-heals before we could observe the stale
        # state. That exact mechanism (cold read of a genuinely stale row, fixed by this cron) was
        # already verified live via `odoo-bin shell` during Phase 3 — see project memory. This test
        # instead confirms the cron method itself runs cleanly and computes the right answer for
        # both an overdue and a not-yet-due order.
        overdue_order = self._make_order('credit', 1000.0, days_ago=40)
        future_order = self._make_order('credit', 1000.0, days_ago=0)

        self.env['sale.order']._cron_update_overdue_status()
        overdue_order.invalidate_recordset()
        future_order.invalidate_recordset()

        self.assertTrue(overdue_order.agro_is_overdue)
        self.assertFalse(future_order.agro_is_overdue)


@tagged('post_install', '-at_install')
class TestAgroWizardLineConstraints(TransactionCase):
    """Tests for the qty/price/discount validation added to both wizards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sell_product = cls.env['product.template'].create({
            'name': 'Test Constraint Product (Sell)', 'type': 'consu', 'is_sellable': True,
        })
        cls.buy_product = cls.env['product.template'].create({
            'name': 'Test Constraint Product (Buy)', 'type': 'consu', 'is_purchasable': True,
        })
        cls.customer = cls.env['res.partner'].create({'name': 'Test Constraint Customer'})
        cls.supplier = cls.env['res.partner'].create({'name': 'Test Constraint Supplier'})

    def test_sale_line_rejects_zero_quantity(self):
        wizard = self.env['agro.sale.wizard'].create({'customer_id': self.customer.id})
        with self.assertRaises(UserError):
            self.env['agro.sale.wizard.line'].create({
                'wizard_id': wizard.id, 'product_id': self.sell_product.id, 'quantity': 0, 'unit_price': 10,
            })

    def test_sale_line_rejects_negative_price(self):
        wizard = self.env['agro.sale.wizard'].create({'customer_id': self.customer.id})
        with self.assertRaises(UserError):
            self.env['agro.sale.wizard.line'].create({
                'wizard_id': wizard.id, 'product_id': self.sell_product.id, 'quantity': 1, 'unit_price': -5,
            })

    def test_sale_line_rejects_discount_over_100(self):
        wizard = self.env['agro.sale.wizard'].create({'customer_id': self.customer.id})
        with self.assertRaises(UserError):
            self.env['agro.sale.wizard.line'].create({
                'wizard_id': wizard.id, 'product_id': self.sell_product.id,
                'quantity': 1, 'unit_price': 10, 'discount_pct': 150,
            })

    def test_purchase_line_rejects_zero_quantity(self):
        wizard = self.env['agro.purchase.wizard'].create({'supplier_id': self.supplier.id})
        with self.assertRaises(UserError):
            self.env['agro.purchase.wizard.line'].create({
                'wizard_id': wizard.id, 'product_id': self.buy_product.id, 'quantity': 0, 'unit_price': 10,
            })

    def test_purchase_line_rejects_negative_price(self):
        wizard = self.env['agro.purchase.wizard'].create({'supplier_id': self.supplier.id})
        with self.assertRaises(UserError):
            self.env['agro.purchase.wizard.line'].create({
                'wizard_id': wizard.id, 'product_id': self.buy_product.id, 'quantity': 1, 'unit_price': -1,
            })
