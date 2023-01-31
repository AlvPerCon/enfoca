import logging

_logger = logging.getLogger(__name__)
from odoo import api, fields, models
import base64
from xml.dom import minidom


class InvoiceSupplierImport(models.Model):
    _name = 'invoice.supplier.import'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Importar XML de Proveedores'

    name = fields.Char(string='Nombre')
    company_id = fields.Many2one('res.company', string='Compañía', required=True,
                                 readonly=False, default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal', string="Diario por defecto", domain=[
        ("type", "=", "purchase")], required=True)
    account_id = fields.Many2one(
        "account.account", string="Cuenta contable por defecto", required=True)
    product_id = fields.Many2one(
        "product.product", string="Producto por defecto", required=True)
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[(
        'res_model', '=', 'invoice.supplier.import')], string='Archivos')
    account_move_ids = fields.One2many(
        "account.move", "invoice_supplier_import_id", string="Facturas de proveedores")
    invoice_count = fields.Integer(
        string='Cantidad de facturas', compute='_compute_invoice_count', readonly=True)

    @api.depends('account_move_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.account_move_ids)

    def action_view_invoice(self):
        """
            Abre el tree de las facturas
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type")
        action['domain'] = [('id', 'in', self.account_move_ids.ids)]
        action['context'] = {
            'default_move_type': 'in_invoice',
        }
        return action

    def action_import_attachments(self):
        """
            Importa solo los XML para convertirlos a facturas
        """
        for attachment in self.attachment_ids:
            if attachment.mimetype.split('/')[1] != 'xml':
                continue
            decoded_data = base64.b64decode(attachment.datas)
            dom = minidom.parseString(decoded_data)
            self.import_invoice_from_xml(
                dom, attachment.datas, attachment.name)
    
    def get_invoice_pdf_from_name(self, name):
        """
            Obtiene el PDF de la factura
        """
        pdf_files = self.attachment_ids.filtered(lambda x: x.name == name)
        if pdf_files:
            pdf_datas =  pdf_files[0].datas
        else:
            pdf_datas = False
        return pdf_datas
   
    def create_model_registry_if_not_exists(self, model, model_field, model_field_value, model_registry_data):
        """
            Crea un registro en el modelo de registro si no existe
        """
        model_registry = self.env[model].search(
            [(model_field, '=', model_field_value)])
        if not model_registry:
            model_registry = self.env[model].create(model_registry_data)
        return model_registry

    def get_taxes_from_xml(self, detail):
        """
            Obtiene los impuestos de la factura XML
        """
        data_taxes_node = detail.getElementsByTagName("cac:TaxSubtotal")
        taxes = []
        for tax_node in data_taxes_node:
            tax_code = tax_node.getElementsByTagName("cac:TaxScheme")[0].getElementsByTagName("cbc:ID")[
                0].firstChild.data
            tax = self.env["account.tax"].search(
                [("type_tax_use", "=", "purchase"), ('l10n_pe_edi_tax_code', '=', tax_code.strip()),
                ("price_include", "=", False)], limit=1)
            taxes.append((4, tax.id, 0))
        return taxes
    
    def get_move_lines_from_xml(self, xml_data):
        """
            Obtiene los lineas de la factura XML
        """
        details = xml_data.getElementsByTagName("cac:InvoiceLine")
        account_move_lines = []
        for detail in details:
            # Producto
            data_producto = detail.getElementsByTagName("cac:Item")[0]
            product_name = data_producto.getElementsByTagName("cbc:Description")[
                0].firstChild.data
            # Cantidad
            data_quantity_node = detail.getElementsByTagName(
                "cbc:InvoicedQuantity")[0]
            quantity = data_quantity_node.firstChild.data
            # Precio unitario
            unit_price = detail.getElementsByTagName(
                "cac:Price")[0].getElementsByTagName("cbc:PriceAmount")[0].firstChild.data
            
            # Impuestos
            taxes = self.get_taxes_from_xml(detail)

            detail_data = (0, 0, {
                "product_id": self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                "name": product_name,
                "quantity": float(quantity),
                "price_unit": float(unit_price),
                "tax_ids": taxes,
                'account_id': self.account_id.id,
            })
            account_move_lines.append(detail_data)
        return account_move_lines
    
    def get_currency_from_xml(self,xml_data):
        """
            Obtiene la moneda de la factura XML
        """
        currency_code = xml_data.getElementsByTagName(
            "cbc:DocumentCurrencyCode")[0].firstChild.data
        currency_id = self.env["res.currency"].search(
            [("name", "=", currency_code)], limit=1)
        return currency_id
    
    def get_document_type_from_xml(self,xml_data):
        """
            Obtiene el tipo de documento de la factura XML
        """
        document_type_code = xml_data.getElementsByTagName("cbc:InvoiceTypeCode")[0].firstChild.data
        document_type_id = self.env["l10n_latam.document.type"].search(
            [("code", "=", document_type_code)], limit=1)
        return document_type_id
    
    def import_invoice_from_xml(self, xml_data, archivo_binario, nombre_binario):
        data_serie = xml_data.getElementsByTagName(
            "cac:Signature")[0].getElementsByTagName("cbc:ID")[0]

        # Create provider
        provider_node = xml_data.getElementsByTagName("cac:SignatoryParty")[0]
        ruc_provider = provider_node.getElementsByTagName("cbc:ID")[
            0].firstChild.data
        provider_data = {
            'name': ruc_provider,
            'company_type': 'company',
            'l10n_latam_identification_type_id': 4,  # RUC
            'vat': ruc_provider
        }
        provider = self.create_model_registry_if_not_exists(
            'res.partner', 'vat', ruc_provider, provider_data)

        # Create account move (Factura de compra)
        invoice_date = xml_data.getElementsByTagName("cbc:IssueDate")[
            0].firstChild.data
        currency_id = self.get_currency_from_xml(xml_data)
        document_type_id = self.get_document_type_from_xml(xml_data)
        data_serie = xml_data.getElementsByTagName(
            "cac:Signature")[0].getElementsByTagName("cbc:ID")[0]
        serie_correlativo = data_serie.firstChild.data
        
        # Detalle de factura
        account_move_lines = self.get_move_lines_from_xml(xml_data)
        
        # PDF
        nombre_pdf = nombre_binario.replace(".xml", ".pdf")
        pdf_binary = self.get_invoice_pdf_from_name(nombre_pdf)
        
        account_move_data = {
            'invoice_user_id': self.env.user.id,
            'partner_id': provider.id,
            'company_id': self.company_id.id,
            'invoice_date': invoice_date,
            'move_type': 'in_invoice',
            "invoice_supplier_import_id": self.id,
            'currency_id': currency_id.id,
            'l10n_latam_document_type_id': document_type_id.id,
            'ref': serie_correlativo,
            'data_xml': archivo_binario,
            'datas_fname': nombre_binario,
            "data_pdf": pdf_binary,
            "datas_fname_pdf": nombre_pdf,
        }

        
        _logger.info("account_move_data")
        _logger.info(account_move_data)
        invoice_id = self.env['account.move'].create(account_move_data)
        _logger.info("invoice_id 1")
        _logger.info(invoice_id)
        
        invoice_id.invoice_line_ids = account_move_lines
        _logger.info("invoice_id 2")
        _logger.info(invoice_id)
        invoice_id._onchange_invoice_line_ids()
        for line in invoice_id.invoice_line_ids:
            line._onchange_account_id()
            line._onchange_price_subtotal()
        
        return invoice_id
  
        #return provider
