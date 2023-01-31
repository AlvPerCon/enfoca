from locale import currency
from odoo import models, api, _, _lt, fields
from itertools import chain
from odoo.tools import float_is_zero
class AccountMulticurrencyRevaluation(models.AbstractModel):
    _inherit = 'account.multicurrency.revaluation'

    filter_analytic = True
    
    def _get_options(self, previous_options=None):
        options = super()._get_options(previous_options)
        rates = self.env['res.currency'].search([('active', '=', True)])._get_rates(self.env.company, options.get('date').get('date_to'))
        for key in rates.keys():  # normalize the rates to the company's currency
            rates[key] /= rates[self.env.company.currency_id.id]
        options['currency_rates'] = {
            str(currency_id.id): {
                'currency_id': currency_id.id,
                'rate_type': currency_id.rate_type,
                'display_name': f"{currency_id.name}/Compra" if currency_id.rate_type == 'purchase' else f"{currency_id.name}/Venta",
                'currency_name': currency_id.name,
                'currency_main': self.env.company.currency_id.name,
                'rate': round(1 / rates[currency_id.id], 3),
            } for currency_id in self.env['res.currency'].search([('active', '=', True)])
        }
        options['company_currency'] = options['currency_rates'].pop(str(self.env.company.currency_id.id))
        options['custom_rate'] = any(
            not float_is_zero(cr['rate'] - rates[cr['currency_id']], 6)
            for cr in options['currency_rates'].values()
        )
        options['warning_multicompany'] = len(self.env.companies) > 1
        return options
    
    # TODO colocar caso donde no se seleccione el SLQ query por defecto
    def _get_sql(self):
        options = self.env.context['report_options']
        query = '(VALUES {}) AS custom_currency_table(currency_id, currency_name, rate_type, rate)'.format(
            ', '.join("(%s, %s, %s, %s)" for i in range(
                len(options['currency_rates'])))
        )
        params = list(chain.from_iterable(
            (cur['currency_id'], cur['currency_name'], cur['rate_type'], cur['rate']) for cur in options['currency_rates'].values()))
        custom_currency_table = self.env.cr.mogrify(
            query, params).decode(self.env.cr.connection.encoding)
        return """
            SELECT {move_line_fields},
                   aml.amount_currency                                  AS report_amount_currency,
                   aml.balance                                          AS report_balance,
                   aml.amount_currency * custom_currency_table.rate               AS report_amount_currency_current,
                   aml.amount_currency * custom_currency_table.rate - aml.balance AS report_adjustment,
                   aml.currency_id                                      AS report_currency_id,
                   account.code                                         AS account_code,
                   account.name                                         AS account_name,
                   currency.name                                        AS currency_code,
                   move.ref                                             AS move_ref,
                   move.name                                            AS move_name,
                   NOT EXISTS (
                       SELECT * FROM account_account_exclude_res_currency_provision WHERE account_account_id = account_id AND res_currency_id = aml.currency_id
                   )                                                    AS report_include
            FROM account_move_line aml
            JOIN account_move move ON move.id = aml.move_id
            JOIN account_account account ON aml.account_id = account.id
            JOIN res_currency currency ON currency.id = aml.currency_id
            JOIN {custom_currency_table} ON custom_currency_table.currency_id = account.multirate_currency_id
            WHERE (account.currency_id != aml.company_currency_id OR (account.internal_type IN ('receivable', 'payable') AND (aml.currency_id != aml.company_currency_id)))
            {account_query}
            UNION ALL
            -- Add the lines without currency, i.e. payment in company currency for invoice in foreign currency
            SELECT {move_line_fields},
                   CASE WHEN aml.id = part.credit_move_id THEN -part.debit_amount_currency ELSE -part.credit_amount_currency
                   END                                                  AS report_amount_currency,
                   -part.amount                                         AS report_balance,
                   CASE WHEN aml.id = part.credit_move_id THEN -part.debit_amount_currency ELSE -part.credit_amount_currency
                   END * custom_currency_table.rate                               AS report_amount_currency_current,
                   CASE WHEN aml.id = part.credit_move_id THEN -part.debit_amount_currency ELSE -part.credit_amount_currency
                   END * custom_currency_table.rate - aml.balance                 AS report_adjustment,
                   CASE WHEN aml.id = part.credit_move_id THEN part.debit_currency_id ELSE part.credit_currency_id
                   END                                                  AS report_currency_id,
                   account.code                                         AS account_code,
                   account.name                                         AS account_name,
                   currency.name                                        AS currency_code,
                   move.ref                                             AS move_ref,
                   move.name                                            AS move_name,
                   NOT EXISTS (
                       SELECT * FROM account_account_exclude_res_currency_provision WHERE account_account_id = account_id AND res_currency_id = aml.currency_id
                   )                                                    AS report_include
            FROM account_move_line aml
            JOIN account_move move ON move.id = aml.move_id
            JOIN account_account account ON aml.account_id = account.id
            JOIN account_partial_reconcile part ON aml.id = part.credit_move_id OR aml.id = part.debit_move_id
            JOIN res_currency currency ON currency.id = (CASE WHEN aml.id = part.credit_move_id THEN part.debit_currency_id ELSE part.credit_currency_id END)
            JOIN {custom_currency_table} ON custom_currency_table.currency_id = account.multirate_currency_id
            WHERE (account.currency_id = aml.company_currency_id AND (account.internal_type IN ('receivable', 'payable') AND aml.currency_id = aml.company_currency_id))
        """.format(
            custom_currency_table=custom_currency_table,
            move_line_fields=self._get_move_line_fields('aml'),
            account_query=self._get_account_query(options),
        )
        
    # boceto idea (CASE WHEN aml.debit = 0 THEN 'purchase' ELSE 'sale' END)
    def _get_account_query(self, options):
        account_query = ''
        if options.get('accounts'):
            account_list = options.get('accounts')
            if len(account_list) == 1:
                account = account_list[0]
                account_query = """ AND aml.account_id = %s""" % (
                    str(account))
            else:
                accounts = tuple(list(set(account_list)))
                account_query = """ AND aml.account_id in %s""" % (
                    str(tuple(accounts)))
        return account_query
