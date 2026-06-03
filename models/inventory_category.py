# -*- coding: utf-8 -*-
from odoo import models, fields


class InventoryCategory(models.Model):
    # Shop-specific product grouping (Seeds, Fertilizers, etc.) — not linked to accounting
    _name = 'inventory.category'
    _description = 'Product Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    product_count = fields.Integer(compute='_compute_product_count', string='Products')

    def _compute_product_count(self):
        # Single read_group query for all categories — avoids N+1 (one query per category)
        counts = self.env['product.template'].read_group(
            domain=[('agro_category_id', 'in', self.ids)],
            fields=['agro_category_id'],
            groupby=['agro_category_id'],
        )
        count_map = {row['agro_category_id'][0]: row['agro_category_id_count'] for row in counts}
        for cat in self:
            cat.product_count = count_map.get(cat.id, 0)
