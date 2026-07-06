# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request


class AgroDashboardController(http.Controller):
    """
    JSON-RPC endpoints for the Agro Business Dashboard OWL component.
    All computation delegated to agro.dashboard model — controller is dispatch-only.
    """

    @http.route('/agro/dashboard/quick_summary', type='json', auth='user')
    def quick_summary(self):
        return request.env['agro.dashboard'].get_quick_summary()

    @http.route('/agro/dashboard/sales_kpis', type='json', auth='user')
    def sales_kpis(self):
        return request.env['agro.dashboard'].get_sales_kpis()

    @http.route('/agro/dashboard/profit_kpis', type='json', auth='user')
    def profit_kpis(self):
        return request.env['agro.dashboard'].get_profit_kpis()

    @http.route('/agro/dashboard/cost_analysis', type='json', auth='user')
    def cost_analysis(self):
        return request.env['agro.dashboard'].get_cost_analysis()

    @http.route('/agro/dashboard/outstanding', type='json', auth='user')
    def outstanding(self):
        return request.env['agro.dashboard'].get_outstanding_analysis()

    @http.route('/agro/dashboard/invoice_summary', type='json', auth='user')
    def invoice_summary(self):
        return request.env['agro.dashboard'].get_invoice_summary()

    @http.route('/agro/dashboard/payment_summary', type='json', auth='user')
    def payment_summary(self, date_from=None, date_to=None):
        return request.env['agro.dashboard'].get_payment_summary(date_from, date_to)

    @http.route('/agro/dashboard/category_performance', type='json', auth='user')
    def category_performance(self, date_from=None, date_to=None):
        return request.env['agro.dashboard'].get_category_performance(date_from, date_to)

    @http.route('/agro/dashboard/top_products', type='json', auth='user')
    def top_products(self, limit=10, date_from=None, date_to=None, order_by='sales'):
        return request.env['agro.dashboard'].get_top_products(limit, date_from, date_to, order_by)

    @http.route('/agro/dashboard/low_stock', type='json', auth='user')
    def low_stock(self):
        return request.env['agro.dashboard'].get_low_stock_products()

    @http.route('/agro/dashboard/dead_stock', type='json', auth='user')
    def dead_stock(self, months=3):
        return request.env['agro.dashboard'].get_dead_stock_products(months)

    @http.route('/agro/dashboard/sales_trend', type='json', auth='user')
    def sales_trend(self, period='monthly'):
        return request.env['agro.dashboard'].get_sales_trend(period)

    @http.route('/agro/dashboard/mom_comparison', type='json', auth='user')
    def mom_comparison(self):
        return request.env['agro.dashboard'].get_mom_comparison()

    @http.route('/agro/dashboard/yoy_comparison', type='json', auth='user')
    def yoy_comparison(self):
        return request.env['agro.dashboard'].get_yoy_comparison()

    @http.route('/agro/dashboard/best_months', type='json', auth='user')
    def best_months(self):
        return request.env['agro.dashboard'].get_best_months()

    @http.route('/agro/dashboard/village_sales', type='json', auth='user')
    def village_sales(self, date_from=None, date_to=None):
        return request.env['agro.dashboard'].get_village_sales(date_from, date_to)

    @http.route('/agro/dashboard/stock_valuation', type='json', auth='user')
    def stock_valuation(self):
        return request.env['agro.dashboard'].get_stock_valuation()

    @http.route('/agro/dashboard/expiry_analysis', type='json', auth='user')
    def expiry_analysis(self):
        return request.env['agro.dashboard'].get_expiry_analysis()

    @http.route('/agro/dashboard/date_range_report', type='json', auth='user')
    def date_range_report(self, date_from, date_to):
        return request.env['agro.dashboard'].get_date_range_report(date_from, date_to)
