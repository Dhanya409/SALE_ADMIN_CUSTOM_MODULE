from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_limit = fields.Float(
        string="Sale Order Limit",
        config_parameter='sale.sale_order_limit'
    )