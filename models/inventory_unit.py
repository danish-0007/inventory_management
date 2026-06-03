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
        # Single read_group query for all units — avoids N+1 (one query per unit)
        counts = self.env['product.template'].read_group(
            domain=[('agro_unit_id', 'in', self.ids)],
            fields=['agro_unit_id'],
            groupby=['agro_unit_id'],
        )
        count_map = {row['agro_unit_id'][0]: row['agro_unit_id_count'] for row in counts}
        for unit in self:
            unit.product_count = count_map.get(unit.id, 0)
