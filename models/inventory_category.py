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
        # Count products in this category
        for cat in self:
            cat.product_count = self.env['product.template'].search_count([
                ('agro_category_id', '=', cat.id)
            ])
