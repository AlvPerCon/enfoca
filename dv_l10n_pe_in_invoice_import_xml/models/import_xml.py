from odoo import models, fields
import requests
import json
import xmltodict
import base64
from xml.dom import minidom


class import_xml(models.Model):
    _inherit = 'account.move'
    
    invoice_supplier_import_id = fields.Many2one('invoice.supplier.import', string='Importar XML')
    datas_fname = fields.Char("Nombre xml")
    data_xml = fields.Binary(string="XML")
    datas_fname_pdf = fields.Char("Nombre pdf")
    data_pdf = fields.Binary(string="PDF")

    # xml_string to dom.xml
    def xml_string_to_dom_xml(self, xml_string):
        return minidom.parseString(xml_string)

    # Check if the model registry already exists and create it if not
    def create_model_registry_if_not_exists(self, model, model_field, model_field_value, model_registry_data):
        model_registry = self.env[model].search([(model_field, '=', model_field_value)])
        if not model_registry:
            model_registry = self.env[model].create(model_registry_data)
        return model_registry

    # Complete all the fields related to an account move
    def xml_to_json(self):
        obj = ("""<?xml version="1.0" encoding="iso-8859-1"?>
    <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
             xmlns:ccts="urn:un:unece:uncefact:documentation:2" xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
             xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
             xmlns:qdt="urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2"
             xmlns:udt="urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <ext:UBLExtensions>
            <ext:UBLExtension>
                <ext:ExtensionContent>
                    <Signature Id="SignatureFacilERP" xmlns="http://www.w3.org/2000/09/xmldsig#">
                        <SignedInfo>
                            <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
                            <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
                            <Reference URI="">
                                <Transforms>
                                    <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                                </Transforms>
                                <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
                                <DigestValue>RFn9rFBl1WJePjeexRUXz6GHCa4=</DigestValue>
                            </Reference>
                        </SignedInfo>
                        <SignatureValue>
                            VgZsGM4AOcmzEf+mZH/516sVsSY2JB4AUsfL3/WEW/O84Obnu2F9vJUItRmoflIOxm5+8RxEhP8tfUiSasT8dwKHpM2xRx2bkM4BkI7GSfNbeVMTNszBPH7WOpyn/Tx71ibwFi2bwfB1gzGmHDTFj4cyig9fGCROQrmZ5cNHHGexe1XL7vY+qZZECs6lF507qPKUoPYeJGkSsNPwL5UMqRhbF1lwwcIALFwFf/yDIDqo/exZRyGB9sf9T9zZp3aXqLD9VJhlezQCDrkhMmwo/pwTVkYneqcbjLwZNW8+/jZqbnkVfEFdIAmncwGgUpsgfNgNn5O+sF3vevL4SbS0xg==
                        </SignatureValue>
                        <KeyInfo>
                            <X509Data>
                                <X509SubjectName>C=PE, L=LIMA, O=DISTRIBUIDORA MESAJIL HNOS S.A.C., OU=20269315688,
                                    SERIALNUMBER=06875616, CN=MESAJIL LEON ABEL MARCELO, E=facte@facilerp.com, STREET=AV.
                                    GARCILAZO DE LA VEGA NRO. 1261 INT. 213 ---- GAL. GARCILA
                                </X509SubjectName>
                                <X509Certificate>
                                    MIIFIjCCBAqgAwIBAgIIIEVrNxXmAiwwDQYJKoZIhvcNAQELBQAwRjEkMCIGA1UEAwwbTGxhbWEucGUgU0hBMjU2IFN0YW5kYXJkIENBMREwDwYDVQQKDAhMTEFNQS5QRTELMAkGA1UEBhMCUEUwHhcNMTkwNzAyMDIxNjQ2WhcNMjIwNzAxMDIxNjQ2WjCCAQAxRjBEBgNVBAkMPUFWLiBHQVJDSUxBWk8gREUgTEEgVkVHQSBOUk8uIDEyNjEgSU5ULiAyMTMgLS0tLSBHQUwuIEdBUkNJTEExITAfBgkqhkiG9w0BCQEWEmZhY3RlQGZhY2lsZXJwLmNvbTEiMCAGA1UEAwwZTUVTQUpJTCBMRU9OIEFCRUwgTUFSQ0VMTzERMA8GA1UEBRMIMDY4NzU2MTYxFDASBgNVBAsMCzIwMjY5MzE1Njg4MSowKAYDVQQKDCFESVNUUklCVUlET1JBIE1FU0FKSUwgSE5PUyBTLkEuQy4xDTALBgNVBAcMBExJTUExCzAJBgNVBAYTAlBFMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvncF1oNxnGXgkxTLEnP9L+BzzWe9hhAYYknGV5GLGpfOPw6rUL0Hg7FztkMSemJyEExen/COZ+AAGium4A7CszVTchEAgne7/q7aS7hNbdJ7s78v/5LEZ1D3dLBLBdVa5Xjlb89/4AbEkvAQVx6z2372Hh0spSbFmykk3qzrAw/GE872yA3MefkzQOOeThOGbqe4mk6c9tqjNRNXqvIITw4F/KkdIBbg58xlQ5We2dI120HOTaoz2rvoAuj4JL1FyYbGDkltmJHWMZ+vmfukUJs4P7YK8sERW3WFYkZez7CrmLGNA8Cat/BP/WbKik64OOUN1Xa4q51gc9HwaMnGdQIDAQABo4IBVjCCAVIwDAYDVR0TAQH/BAIwADAfBgNVHSMEGDAWgBRdiFut62X7/mii5NlvPVdyou8rmTAwBggrBgEFBQcBAQQkMCIwIAYIKwYBBQUHMAGGFGh0dHA6Ly9vY3NwLmxsYW1hLnBlMB0GA1UdEQQWMBSBEmZhY3RlQGZhY2lsZXJwLmNvbTBGBgNVHSAEPzA9MDsGDSsGAQQBg5d3AAEAAgEwKjAoBggrBgEFBQcCARYcaHR0cHM6Ly9sbGFtYS5wZS9yZXBvc2l0b3J5LzAdBgNVHSUEFjAUBggrBgEFBQcDAgYIKwYBBQUHAwQwOgYDVR0fBDMwMTAvoC2gK4YpaHR0cDovL2NybC5sbGFtYS5wZS9sbGFtYXBlc3RhbmRhcmRjYS5jcmwwHQYDVR0OBBYEFPhelE23B6xPu63FjkKss8z3DNeKMA4GA1UdDwEB/wQEAwIGwDANBgkqhkiG9w0BAQsFAAOCAQEANUUSg/+XcfqCV+iR7KeglzkNw5sJ0wzGsrnJnDAdXCE60AE3GvJ5ZdT5Qb0MjCw2IvTHE2GtN+d6oTFNGusgIsLGGLfwnBGAeWAXSQ5T+ET9bRwiJE7FRAfug5Ho79rj+V+8fzSjohYECtz6ygg8PiwrhgD0ddnMamkzO8Pw9O6a3fODGxT7PnK3gH0fDUx7BaY+xFI9R+E4xrucg2j+m8Ux39TywwVxV9UGa6MU6JmXh8VhAp8iGcMrpEhmk2on9tMXlnF+TA1xN9/vwauJ7fjykQNrfNj0jt9WTvTVmJfCnfj7NP68G90wN9YyoMum02E9p28qDB/fnzmYDua9pA==
                                </X509Certificate>
                            </X509Data>
                        </KeyInfo>
                    </Signature>
                </ext:ExtensionContent>
            </ext:UBLExtension>
        </ext:UBLExtensions>
        <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
        <cbc:CustomizationID>2.0</cbc:CustomizationID>
        <cbc:ID>F010-1114</cbc:ID>
        <cbc:IssueDate>2022-01-11</cbc:IssueDate>
        <cbc:IssueTime>17:56:23</cbc:IssueTime>
        <cbc:DueDate>2022-01-12</cbc:DueDate>
        <cbc:InvoiceTypeCode listID="0101" listAgencyName="PE:SUNAT" listName="Tipo de Documento"
                             listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01" name="Tipo de Operacion"
                             listSchemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo51">01
        </cbc:InvoiceTypeCode>
        <cbc:Note languageLocaleID="1000">TRESCIENTOS TREINTA Y OCHO Y 68/100</cbc:Note>
        <cbc:DocumentCurrencyCode listID="ISO 4217 Alpha" listAgencyName="United Nations Economic Commission for Europe"
                                  listName="Currency">PEN
        </cbc:DocumentCurrencyCode>
        <cbc:LineCountNumeric>2</cbc:LineCountNumeric>
        <cac:OrderReference>
            <cbc:ID>#37643</cbc:ID>
        </cac:OrderReference>
        <cac:Signature>
            <cbc:ID>20269315688</cbc:ID>
            <cac:SignatoryParty>
                <cac:PartyIdentification>
                    <cbc:ID>20269315688</cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyName>
                    <cbc:Name>DISTRIBUIDORA MESAJIL HNOS. S.A.C.</cbc:Name>
                </cac:PartyName>
            </cac:SignatoryParty>
            <cac:DigitalSignatureAttachment>
                <cac:ExternalReference>
                    <cbc:URI>#SignatureFacilERP</cbc:URI>
                </cac:ExternalReference>
            </cac:DigitalSignatureAttachment>
        </cac:Signature>
        <cac:AccountingSupplierParty>
            <cac:Party>
                <cac:PartyIdentification>
                    <cbc:ID schemeID="6" schemeName="Documento de Identidad" schemeAgencyName="PE:SUNAT"
                            schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">20269315688
                    </cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyName>
                    <cbc:Name>DISTRIBUIDORA MESAJIL HNOS</cbc:Name>
                </cac:PartyName>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>DISTRIBUIDORA MESAJIL HNOS. S.A.C.</cbc:RegistrationName>
                    <cac:RegistrationAddress>
                        <cbc:ID schemeName="Ubigeos" schemeAgencyName="PE:INEI">150101</cbc:ID>
                        <cbc:AddressTypeCode listAgencyName="PE:SUNAT" listName="Establecimientos anexos">0031
                        </cbc:AddressTypeCode>
                        <cbc:CityName>LIMA</cbc:CityName>
                        <cbc:CountrySubentity>LIMA</cbc:CountrySubentity>
                        <cbc:District>LIMA</cbc:District>
                        <cac:AddressLine>
                            <cbc:Line>AV. GARCILAZO DE LA VEGA 1261 INT. 213 GAL. GARCILAZO DE LA VEGA</cbc:Line>
                        </cac:AddressLine>
                        <cac:Country>
                            <cbc:IdentificationCode listID="ISO 3166-1"
                                                    listAgencyName="United Nations Economic Commission for Europe"
                                                    listName="Country">PE
                            </cbc:IdentificationCode>
                        </cac:Country>
                    </cac:RegistrationAddress>
                </cac:PartyLegalEntity>
            </cac:Party>
        </cac:AccountingSupplierParty>
        <cac:AccountingCustomerParty>
            <cac:Party>
                <cac:PartyIdentification>
                    <cbc:ID schemeID="6" schemeName="Documento de Identidad" schemeAgencyName="PE:SUNAT"
                            schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">20514733962
                    </cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>ENFOCA - SOCIEDAD ADMINISTRADORA DE FONDOS DE INVERSION S.A.
                    </cbc:RegistrationName>
                </cac:PartyLegalEntity>
            </cac:Party>
        </cac:AccountingCustomerParty>
        <cac:PaymentTerms>
            <cbc:ID>FormaPago</cbc:ID>
            <cbc:PaymentMeansID>Contado</cbc:PaymentMeansID>
        </cac:PaymentTerms>
        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="PEN">51.66</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="PEN">287.02</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="PEN">51.66</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cac:TaxScheme>
                        <cbc:ID schemeID="UN/ECE 5153" schemeName="Codigo de tributos" schemeAgencyName="PE:SUNAT">1000
                        </cbc:ID>
                        <cbc:Name>IGV</cbc:Name>
                        <cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>
        <cac:LegalMonetaryTotal>
            <cbc:LineExtensionAmount currencyID="PEN">287.02</cbc:LineExtensionAmount>
            <cbc:TaxInclusiveAmount currencyID="PEN">338.68</cbc:TaxInclusiveAmount>
            <cbc:AllowanceTotalAmount currencyID="PEN">0.00</cbc:AllowanceTotalAmount>
            <cbc:ChargeTotalAmount currencyID="PEN">0.00</cbc:ChargeTotalAmount>
            <cbc:PrepaidAmount currencyID="PEN">0.00</cbc:PrepaidAmount>
            <cbc:PayableAmount currencyID="PEN">338.68</cbc:PayableAmount>
        </cac:LegalMonetaryTotal>
        <cac:InvoiceLine>
            <cbc:ID>1</cbc:ID>
            <cbc:InvoicedQuantity unitCode="NIU" unitCodeListID="UN/ECE rec 20"
                                  unitCodeListAgencyName="United Nations Economic Commission for Europe">1.0000
            </cbc:InvoicedQuantity>
            <cbc:LineExtensionAmount currencyID="PEN">278.54</cbc:LineExtensionAmount>
            <cac:PricingReference>
                <cac:AlternativeConditionPrice>
                    <cbc:PriceAmount currencyID="PEN">328.68000000</cbc:PriceAmount>
                    <cbc:PriceTypeCode listAgencyName="PE:SUNAT" listName="Tipo de Precio"
                                       listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16">01
                    </cbc:PriceTypeCode>
                </cac:AlternativeConditionPrice>
            </cac:PricingReference>
            <cac:TaxTotal>
                <cbc:TaxAmount currencyID="PEN">50.14</cbc:TaxAmount>
                <cac:TaxSubtotal>
                    <cbc:TaxableAmount currencyID="PEN">278.54</cbc:TaxableAmount>
                    <cbc:TaxAmount currencyID="PEN">50.14</cbc:TaxAmount>
                    <cac:TaxCategory>
                        <cbc:Percent>18.00</cbc:Percent>
                        <cbc:TaxExemptionReasonCode listAgencyName="PE:SUNAT" listName="Afectacion del IGV"
                                                    listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07">10
                        </cbc:TaxExemptionReasonCode>
                        <cac:TaxScheme>
                            <cbc:ID schemeID="UN/ECE 5153" schemeName="Codigo de tributos" schemeAgencyName="PE:SUNAT">
                                1000
                            </cbc:ID>
                            <cbc:Name>IGV</cbc:Name>
                            <cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
                        </cac:TaxScheme>
                    </cac:TaxCategory>
                </cac:TaxSubtotal>
            </cac:TaxTotal>
            <cac:Item>
                <cbc:Description>Teclado + Mouse Microsoft Ergonomic Desktop</cbc:Description>
                <cac:SellersItemIdentification>
                    <cbc:ID>022453</cbc:ID>
                </cac:SellersItemIdentification>
            </cac:Item>
            <cac:Price>
                <cbc:PriceAmount currencyID="PEN">278.54237288</cbc:PriceAmount>
            </cac:Price>
        </cac:InvoiceLine>
        <cac:InvoiceLine>
            <cbc:ID>2</cbc:ID>
            <cbc:InvoicedQuantity unitCode="ZZ" unitCodeListID="UN/ECE rec 20"
                                  unitCodeListAgencyName="United Nations Economic Commission for Europe">1.0000
            </cbc:InvoicedQuantity>
            <cbc:LineExtensionAmount currencyID="PEN">8.47</cbc:LineExtensionAmount>
            <cac:PricingReference>
                <cac:AlternativeConditionPrice>
                    <cbc:PriceAmount currencyID="PEN">10.00000000</cbc:PriceAmount>
                    <cbc:PriceTypeCode listAgencyName="PE:SUNAT" listName="Tipo de Precio"
                                       listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16">01
                    </cbc:PriceTypeCode>
                </cac:AlternativeConditionPrice>
            </cac:PricingReference>
            <cac:TaxTotal>
                <cbc:TaxAmount currencyID="PEN">1.53</cbc:TaxAmount>
                <cac:TaxSubtotal>
                    <cbc:TaxableAmount currencyID="PEN">8.47</cbc:TaxableAmount>
                    <cbc:TaxAmount currencyID="PEN">1.53</cbc:TaxAmount>
                    <cac:TaxCategory>
                        <cbc:Percent>18.00</cbc:Percent>
                        <cbc:TaxExemptionReasonCode listAgencyName="PE:SUNAT" listName="Afectacion del IGV"
                                                    listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07">10
                        </cbc:TaxExemptionReasonCode>
                        <cac:TaxScheme>
                            <cbc:ID schemeID="UN/ECE 5153" schemeName="Codigo de tributos" schemeAgencyName="PE:SUNAT">
                                1000
                            </cbc:ID>
                            <cbc:Name>IGV</cbc:Name>
                            <cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
                        </cac:TaxScheme>
                    </cac:TaxCategory>
                </cac:TaxSubtotal>
            </cac:TaxTotal>
            <cac:Item>
                <cbc:Description>POR ENVIO DE MERCADERIA</cbc:Description>
                <cac:SellersItemIdentification>
                    <cbc:ID>017271</cbc:ID>
                </cac:SellersItemIdentification>
            </cac:Item>
            <cac:Price>
                <cbc:PriceAmount currencyID="PEN">8.47457627</cbc:PriceAmount>
            </cac:Price>
        </cac:InvoiceLine>
    </Invoice>
                   """)
        xml_data = self.xml_string_to_dom_xml(obj)

        # Create provider
        provider_node = xml_data.getElementsByTagName("cac:SignatoryParty")[0]
        ruc_provider = provider_node.getElementsByTagName("cbc:ID")[0].firstChild.data
        provider_data = {
            'name': ruc_provider,
            'company_type': 'company',
            'l10n_latam_identification_type_id': 4,  # RUC
            'vat': ruc_provider
        }
        provider = self.create_model_registry_if_not_exists('res.partner', 'vat', ruc_provider, provider_data)
        print("provider", provider)

        # Create account move line (Detalle de factura)
        account_move_lines = []
        details = xml_data.getElementsByTagName("cac:InvoiceLine")
        for detail in details:
            # Create product
            data_producto = detail.getElementsByTagName("cac:Item")[0]
            product_name = data_producto.getElementsByTagName("cbc:Description")[0].firstChild.data
            product_data = {
                'name': product_name,
                'barcode': product_name,
                'default_code': product_name,
                'detailed_type': 'product',  # consumible?
            }
            product = self.create_model_registry_if_not_exists('product.product', 'barcode', product_name, product_data)

            # Complete detail data
            # Quantity
            data_quantity_node = detail.getElementsByTagName("cbc:InvoicedQuantity")[0]
            quantity = data_quantity_node.firstChild.data

            # Unit price
            unit_price = detail.getElementsByTagName("cac:Price")[0].getElementsByTagName("cbc:PriceAmount")[
                0].firstChild.data

            # Taxes
            data_taxes_node = detail.getElementsByTagName("cac:TaxSubtotal")
            taxes = []
            for tax_node in data_taxes_node:
                tax_code = tax_node.getElementsByTagName("cac:TaxScheme")[0].getElementsByTagName("cbc:ID")[
                    0].firstChild.data
                tax = self.env["account.tax"].search(
                    [("type_tax_use", "=", "purchase"), ('l10n_pe_edi_tax_code', '=', tax_code.strip()),
                     ("price_include", "=", False)], limit=1)
                taxes.append(tax.id)

            print("taxes", taxes)
            detail_data = {
                "product_id": product.id,
                'product_uom_id': product.uom_id.id,
                "name": product_name,
                "quantity": float(quantity),
                "price_unit": float(unit_price),
                "tax_ids": taxes,
                'account_id': 1,
            }
            account_move_lines.append(detail_data)

        # Create account move (Factura de compra)
        invoice_date = xml_data.getElementsByTagName("cbc:IssueDate")[0].firstChild.data

        # Currency
        currency = xml_data.getElementsByTagName("cbc:DocumentCurrencyCode")[0].firstChild.data
        print("juju", currency.strip(), type(currency))
        currency_odoo = self.env['res.currency'].search([('name', '=', currency.strip())])
        print("currency0", currency_odoo)

        document_type = self.env["l10n_latam.document.type"].search([("name", "=", "Factura")], limit=1)
        data_serie = xml_data.getElementsByTagName("cac:Signature")[0].getElementsByTagName("cbc:ID")[0]
        serie_correlativo = data_serie.firstChild.data

        account_move_data = {
            'partner_id': provider.id,
            'company_id': self.env.company.id,
            'invoice_date': invoice_date,
            'move_type': 'in_invoice',
            # "xml_import_id": self.id,
            'currency_id': currency_odoo.id,
            'l10n_latam_document_type_id': document_type.id,  # Ruc,
            'ref': serie_correlativo,
            # "data_xml": archivo_binario,
            # "datas_fname": nombre_binario,
            # "data_pdf": pdf_binary,
            # "datas_fname_pdf": nombre_pdf,
            'invoice_line_ids': account_move_lines
        }

        print("aaaa", account_move_lines)
        # factura = self.env['account.move'].create(account_move_data)

        invoice = self.env['account.move'].create(account_move_data)
        invoice._onchange_invoice_line_ids()
        for line in invoice.invoice_line_ids:
            line._onchange_account_id()
            line._onchange_price_subtotal()
