from odoo import models, fields, _, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_supplier_import_id = fields.Many2one(
        'invoice.supplier.import', string='Importar XML')
    datas_fname = fields.Char("Nombre xml")
    data_xml = fields.Binary(string="XML")
    datas_fname_pdf = fields.Char("Nombre pdf")
    data_pdf = fields.Binary(string="PDF")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.constrains('account_id', 'journal_id')
    def _check_constrains_account_id_journal_id(self):
        for line in self.filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
            account = line.account_id
            journal = line.move_id.journal_id

            if account.deprecated:
                raise UserError(_('The account %s (%s) is deprecated.') % (
                    account.name, account.code))

            account_currency = account.currency_id
            _logger.info(account)
            _logger.info(account.currency_id)
            _logger.info(line)
            _logger.info(line.company_currency_id)
            _logger.info(line.currency_id)
            if account_currency and account_currency != line.company_currency_id and account_currency != line.currency_id:
                raise UserError(
                    _('The account selected on your journal entry forces to provide a secondary currency. You should remove the secondary currency on the account.'))

            if account.allowed_journal_ids and journal not in account.allowed_journal_ids:
                raise UserError(
                    _('You cannot use this account (%s) in this journal, check the field \'Allowed Journals\' on the related account.', account.display_name))

            failed_check = False
            if (journal.type_control_ids - journal.default_account_id.user_type_id) or journal.account_control_ids:
                failed_check = True
                if journal.type_control_ids:
                    failed_check = account.user_type_id not in (
                        journal.type_control_ids - journal.default_account_id.user_type_id)
                if failed_check and journal.account_control_ids:
                    failed_check = account not in journal.account_control_ids
