# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AgroTaxRate(models.Model):
    _name = 'agro.tax.rate'
    _description = 'Tax Rate'
    _order = 'rate'

    name = fields.Char(string='Name', required=True)
    rate = fields.Float(string='Rate (%)', required=True, digits=(5, 2))
    # Two account.tax records: one for adding tax on top, one for extracting tax from inclusive price
    account_tax_excl_id = fields.Many2one(
        'account.tax', string='Tax (Excl.)', readonly=True, copy=False,
        help='Used when sale price does NOT include tax — tax is added on top.'
    )
    account_tax_incl_id = fields.Many2one(
        'account.tax', string='Tax (Incl.)', readonly=True, copy=False,
        help='Used when sale price already includes tax — Odoo back-calculates the breakdown.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._sync_account_taxes()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'name' in vals or 'rate' in vals:
            for rec in self:
                rec._sync_account_taxes()
        return res

    def _sync_account_taxes(self):
        Tax = self.env['account.tax']
        country = (self.env.company.country_id
                   or self.env.ref('base.in', raise_if_not_found=False))
        base_vals = {
            'amount': self.rate,
            'type_tax_use': 'sale',
            'amount_type': 'percent',
        }
        if country:
            base_vals['country_id'] = country.id
        if not self.account_tax_excl_id:
            self.account_tax_excl_id = Tax.create({
                **base_vals,
                'name': self.name,
                'price_include': False,
            })
        else:
            self.account_tax_excl_id.write({'name': self.name, 'amount': self.rate})

        incl_name = f'{self.name} (incl.)'
        if not self.account_tax_incl_id:
            self.account_tax_incl_id = Tax.create({
                **base_vals,
                'name': incl_name,
                'price_include': True,
            })
        else:
            self.account_tax_incl_id.write({'name': incl_name, 'amount': self.rate})
