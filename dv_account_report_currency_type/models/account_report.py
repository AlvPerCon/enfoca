# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountReport(models.AbstractModel):
    _inherit = "account.report"

    filter_currency_type = None

    @api.model
    def _init_filter_analytic(self, options, previous_options=None):
        super(AccountReport, self)._init_filter_analytic(options, previous_options)
        if not self.filter_analytic:
            return
            
        options["accounts"] = previous_options and previous_options.get("accounts") or []
        account_ids = [int(acc) for acc in options["accounts"]]
        selected_accounts = account_ids \
                            and self.env["account.account"].browse(account_ids) \
                            or self.env["account.account"]
        options["selected_account_names"] = selected_accounts.mapped("name")

        if self.filter_currency_type:
            options['available_currency_types'] = [{'id':1,'name':'Compra'},{'id':2,'name':'Venta'}]
            options['currency_type'] = (previous_options or {}).get('currency_type') 
                
            if options['currency_type'] not in [1, 2]:
                # Replace the report in options by the default report if it is not the generic report
                # (always available for all companies) and the report in options is not available for this company
                options['currency_type'] = 1
            
            
    
    @api.model
    def _get_options_analytic_domain(self, options):
        domain = super(AccountReport, self)._get_options_analytic_domain(options)
        if options.get("accounts"):
            account_ids = [int(acc) for acc in options["accounts"]]
            domain.append(("account_id", "in", account_ids))
        return domain
    
    def _set_context(self, options):
        ctx = super(AccountReport, self)._set_context(options)
        if options.get("accounts"):
            ctx["account_ids"] = self.env["account.account"].browse([int(acc) for acc in options["accounts"]])
        return ctx
    
    def get_report_informations(self, options):
        info = super(AccountReport, self).get_report_informations(options)
        options = options or self._get_options(options)
        if options.get("accounts") is not None:
            info["options"]["selected_account_names"] = [self.env["account.account"].browse(int(account)).name for account in options["accounts"]]
        return info
