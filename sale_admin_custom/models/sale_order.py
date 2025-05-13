from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manager_reference = fields.Char("Manager Reference")
    auto_workflow     = fields.Boolean("Auto Workflow")

    def write(self, vals):
        # Prevent non–Sale Admins (e.g. Sales Managers) from editing Manager Reference
        if 'manager_reference' in vals and not self.env.user.has_group('sale_admin_custom.group_sale_admin'):
            raise UserError("Only Sale Admin can modify the Manager Reference field.")
        return super().write(vals)

    def action_confirm(self):
        # 1) enforce the configured sale order limit
        limit = float(
            self.env['ir.config_parameter']
            .sudo()
            .get_param('sale_admin_custom.sale_order_limit', default=0)
        )
        for order in self:
            if order.amount_total > limit and \
                    not self.env.user.has_group('sale_admin_custom.group_sale_admin'):
                raise UserError(_("Only Sale Admin can confirm orders exceeding the limit."))

        # 2) no issues → proceed with the built-in confirmation
        return super(SaleOrder, self).action_confirm()

        # 2) run the built-in confirmation logic
        res = super().action_confirm()

        # 3) if Auto Workflow is checked, complete deliveries → invoices → payments
        for order in self.filtered('auto_workflow'):

            # —–––––– DELIVERIES –––––—
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                if picking.state == 'draft':
                    picking.action_confirm()
                if picking.state in ('confirmed', 'assigned', 'partially_available'):
                    picking.action_assign()
                for ml in picking.move_line_ids:
                    ml.qty_done = ml.move_id.product_uom_qty
                picking.with_context(skip_backorder=True).button_validate()

            # —–––––– INVOICING –––––—
            invoices = order._create_invoices()
            invoices.action_post()

            # —–––––– PAYMENTS –––––—
            for inv in invoices:
                ctx = {
                    'active_model':       'account.move',
                    'active_ids':         inv.ids,
                    'default_journal_id': (
                        self.env['account.journal']
                            .search([('type', '=', 'bank')], limit=1)
                            .id
                    ),
                    'default_payment_method_id': (
                        self.env.ref('account.account_payment_method_manual_in').id
                    ),
                    'default_payment_type':   'inbound',
                    'default_amount':         inv.amount_residual,
                    'default_payment_date':   fields.Date.context_today(self),
                }
                wizard = (
                    self.env['account.payment.register']
                        .with_context(ctx)
                        .create({})
                )
                wizard.action_create_payments()

        return res
