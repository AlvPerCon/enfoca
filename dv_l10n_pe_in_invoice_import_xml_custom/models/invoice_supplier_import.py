from odoo import api, fields, models


class InvoiceSupplierImport(models.Model):
    _inherit = 'invoice.supplier.import'

    def get_currency_from_xml(self, xml_data):
        """
            Obtiene la moneda de la factura XML
        """
        currency_code = xml_data.getElementsByTagName(
            "cbc:DocumentCurrencyCode")[0].firstChild.data
        currency_id = self.env["res.currency"].search(
            [("name", "=", currency_code), ('rate_type', '=', 'sell')], limit=1)
        return currency_id
