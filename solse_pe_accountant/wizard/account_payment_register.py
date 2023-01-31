# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    es_detraccion_retencion = fields.Boolean(
        "Es por Detracción/Retención", help="Marcar si el pago es por la detracción o retención")
    communication = fields.Char(
        string="Memo", store=True, readonly=False, compute='_compute_communication_2')
    transaction_number = fields.Char(string='Número de operación')

    @api.depends('can_edit_wizard', 'line_ids')
    def _compute_communication_2(self):
        for wizard in self:
            if wizard.can_edit_wizard:
                factura = wizard.line_ids[0].move_id
                if factura:
                    dato = factura.name
                    partes = dato.split(" ")
                    dato = partes[1] if len(partes) == 2 else partes[0]
                    wizard.communication = dato
                else:
                    batches = wizard._get_batches()
                    wizard.communication = wizard._get_batch_communication(
                        batches[0])

            else:
                factura = wizard.line_ids[0].move_id
                if factura:
                    dato = factura.name
                    partes = dato.split(" ")
                    dato = dato if len(partes) == 1 else dato[1]
                    wizard.communication = dato
                else:
                    wizard.communication = False

    @api.onchange('es_detraccion_retencion', 'journal_id')
    def _onchange_detraccion_retencion(self):
        factura = self.line_ids[0].move_id
        self.payment_difference_handling = "open"
        if self.es_detraccion_retencion:
            self.currency_id = self.env.ref('base.PEN')
            self.amount = factura.monto_detraccion + factura.monto_retencion
        else:
            self.currency_id = factura.currency_id
            self.amount = self.source_amount_currency - \
                factura.monto_detraccion_base - factura.monto_retencion_base

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister,
                             self)._create_payment_vals_from_wizard()
        payment_vals['transaction_number'] = self.transaction_number
        return payment_vals

    def _create_payments(self):
        self.ensure_one()
        res = super(AccountPaymentRegister, self)._create_payments()
        factura = self.line_ids[0].move_id
        factura.pago_detraccion = res.id
        return res
