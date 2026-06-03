# -*- coding: utf-8 -*-
from odoo import models, fields


class InventoryUnit(models.Model):
    # Stores custom units (kg, litre, bag, etc.) — simpler than Odoo's built-in UOM
    _name = 'inventory.unit'
    _description = 'Unit of Measure'
    _order = 'category, name'

    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    category = fields.Selection([
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('count', 'Count'),
    ], string='Category', required=True)
    active = fields.Boolean(default=True)
    product_count = fields.Integer(compute='_compute_product_count', string='Products')

    def _compute_product_count(self):
        # Count products using this unit — shown as a stat on the form
        for unit in self:
            unit.product_count = self.env['product.template'].search_count([
                ('agro_unit_id', '=', unit.id)
            ])
