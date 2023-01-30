# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import base64
import logging
_logging = logging.getLogger(__name__)

class Telecredito(models.Model):
	_name = "speru.telecredito"
	_description = "Generacion de txt para pagos"

	name = fields.Char('Nombre Lote')
	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	company_currency_id = fields.Many2one(string='Moneda de la empresa', readonly=True, related='company_id.currency_id')
	cant_abonos = fields.Integer('Cant. Abonos')
	fecha = fields.Date('Fecha')
	tipo_cuenta = fields.Selection([('C', 'Corriente'), ('M', 'Maestra')], string='Tipo cuenta', default='C')
	cuenta_cargo = fields.Many2one('account.journal', 'Cuenta Cargo', domain=[('type', '=', 'bank')])
	monto_total = fields.Monetary('Monto total', currency_field='company_currency_id', compute="_compute_monto_total", store=True)
	referencia = fields.Char('Referencia')
	state = fields.Selection([('borrador', 'Borrador'), ('confirmado', 'Confirmado')], default='borrador', string='Estado')

	pago_ids = fields.One2many('account.payment', 'telecredito_id', string='Pagos realizados')
	factura_ids = fields.One2many('account.move', 'telecredito_id', string='Facturas a presentar')

	telecredito_txt_01 = fields.Text(string='Contenido del TXT')
	telecredito_txt_01_binary = fields.Binary(string='TXT', readonly=True)
	telecredito_txt_01_filename = fields.Char(string='Nombre del TXT')

	@api.depends('factura_ids', 'factura_ids.monto_neto_pagar_base')
	def _compute_monto_total(self):
		for reg in self:
			total = 0
			for linea in reg.factura_ids:
				total = total + linea.monto_neto_pagar_base
				for rel in linea.reversal_move_id:
					total = total - rel.monto_neto_pagar_base
			reg.monto_total = total

	def crear_txt_proveedor(self):
		if not self.fecha:
			raise Warning('No se ha establecido fecha')
		if not self.cuenta_cargo:
			raise Warning('No se ha establecido cuenta bancaria')

		array_retorno = []
		datos_cabecera = self.obtener_datos_cabecera()
		array_retorno = array_retorno + datos_cabecera[0]
		monto_cargo = datos_cabecera[1]
		monto_abono = 0
		txt_string_01 = ''
		proveedores = self.factura_ids.mapped('partner_id')
		for proveedor in proveedores:
			datos_respuesta = self.obtener_detalles_facturas_provedor(proveedor, monto_abono)
			string_detalle = datos_respuesta[0]
			monto_abono = datos_respuesta[1]
			txt_string_01 = txt_string_01+'\r\n'+ string_detalle

		"""return
		for factura in self.factura_ids:
			datos_respuesta = self.obtener_detalles_factura(factura, monto_abono)
			string_detalle = datos_respuesta[0]
			monto_abono = datos_respuesta[1]
			txt_string_01 = txt_string_01+'\r\n'+ string_detalle
		"""

		monto_cargo = float(monto_cargo)
		monto_abono = float(monto_abono)
		suma_montos = monto_cargo + monto_abono
		suma_montos = round(suma_montos, 2)
		suma_string = str(suma_montos).split(".")[0]
		suma_string = self.completar_campo_izquierda(suma_string, "0", 15)

		fecha_array = str(self.fecha).split('-')
		name_01 = "PROVEEDORES"+fecha_array[0]+""+fecha_array[1]+""+fecha_array[2]
		lines_to_write_01 = []
		array_retorno.append(suma_string)
		lines_to_write_01.append(''.join(array_retorno))
		lines_to_write_01.append('')
		txt_string_00 = ''.join(lines_to_write_01)

		txt_completo = txt_string_00 + txt_string_01
		self.telecredito_txt_01 = txt_completo
		self.telecredito_txt_01_binary = base64.b64encode(txt_completo.encode())
		self.telecredito_txt_01_filename = name_01 + '.txt'


	def obtener_datos_cabecera(self):
		datos = []
		datos.append('1')
		cant = str(len(self.factura_ids))
		txt_cant = self.completar_campo_izquierda(cant, '0', 6)
		# 2 (Cant. abonos)
		datos.append(txt_cant)
		if self.fecha:
			fecha = str(self.fecha)
			fecha_txt_split = fecha.split('-')
			fecha_txt = fecha_txt_split[0]+''+fecha_txt_split[1]+''+fecha_txt_split[2]
			# 3 (F. proc)
			datos.append(fecha_txt)
		# 4 (Tipo de Cuenta de cargo)
		datos.append(self.tipo_cuenta)
		# 5
		datos.append('0001')
		# 6 (Cuenta de cargo)
		cuenta_cargo = self.cuenta_cargo.bank_account_id.acc_number
		cuenta_cargo = cuenta_cargo.replace('-', '')
		cuenta_cargo = cuenta_cargo.replace(' ', '')
		cant_digitos = 13
		cuenta_cargo_completo = self.completar_campo_derecha(cuenta_cargo, ' ', cant_digitos)
		datos.append(cuenta_cargo_completo)
		# espacios en blanco
		datos.append(self.completar_campo_derecha("", " ", 7))
		# 7 (Monto total-14 y 2 decimales)
		monto_total = str(self.monto_total)
		partes_monto_total = monto_total.split(".")
		parte_entera = self.completar_campo_izquierda(partes_monto_total[0], '0', 14)
		parte_decimal = str(partes_monto_total[1])
		if len(parte_decimal) == 1:
			parte_decimal = ""+parte_decimal + "0"
		elif len(parte_decimal) == 0:
			parte_decimal = "00"

		datos.append(parte_entera+"."+parte_decimal)
		# 8 Referencia - 40
		referencia = self.referencia or ""
		referencia = self.completar_campo_derecha(referencia, " ", 40)
		datos.append(referencia)
		# 9 (Flag exoneracion de igv)
		datos.append("N")
		total_cargo = cuenta_cargo[4: len(cuenta_cargo) - 3]
		return [datos, total_cargo]

	def obtener_detalles_facturas_provedor(self, proveedor, monto_abono):
		linea_cabecera = []
		# 1 
		linea_cabecera.append('2')
		# 2 (Tip. Cnt de Abono)
		banco = self.obtener_cuenta_entidad(proveedor)
		tipo_cuenta = self.cuenta_cargo.bank_account_id.tipo_cuenta
		linea_cabecera.append(banco.tipo_cuenta)
		# 3 (Cuenta de Abono)
		numero_cuenta = banco.acc_number
		numero_cuenta = numero_cuenta.replace('-', '')
		numero_cuenta = numero_cuenta.replace(' ', '')
		"""cant_cart = 13
		if tipo_cuenta == 'A':
			cant_cart = 14
		elif tipo_cuenta == 'B':
			cant_cart = 20"""
		cant_cart = 20
		linea_cabecera.append(self.completar_campo_derecha(numero_cuenta, ' ', cant_cart))
		# 4
		linea_cabecera.append('1')
		# 5 (tipo de documento)
		linea_cabecera.append(proveedor.doc_type)
		# 6 (nro doc indentidad - 12 caracteres completando a la derecha)  + 3 espacios vacios
		doc_number = proveedor.doc_number
		linea_cabecera.append(self.completar_campo_derecha(doc_number, ' ', 15))
		"""# 6.1
		linea_cabecera.append('       ')"""
		# 7 (Nombre prov - 75)
		nombre_entidad = proveedor.display_name
		linea_cabecera.append(self.completar_campo_derecha(nombre_entidad, ' ', 75))
		# 8
		ref_b = 'Referencia Beneficiario '+proveedor.doc_number
		linea_cabecera.append(self.completar_campo_derecha(ref_b, ' ', 40))
		# 9
		ref_e = 'Ref Emp '+proveedor.doc_number
		linea_cabecera.append(self.completar_campo_derecha(ref_e, ' ', 20))
		# 10 (Cantidad de documentos)
		linea_cabecera.append('0001')
		
		########################## Inicio de detalles
		facturas = self.factura_ids.filtered(lambda p: p.partner_id.id == proveedor.id)
		total_credito = 0.0
		total_facturas = 0.0
		lineas_detalles = ''
		for factura in facturas:
			detalle_n1 = []
			# 1
			detalle_n1.append('3')
			# 2 (Tipo de Documento a pagar)
			detalle_n1.append('F')
			# 3 (Nro. del Documento - 15)
			nro_doc = factura.ref
			detalle_n1.append(self.completar_campo_izquierda(nro_doc, '0', 15))
			# 4 (Monto del Documento - 14 y 2 decimales)
			monto = factura.monto_neto_pagar_base
			total_facturas = total_facturas + monto
			monto = str(monto)
			partes_monto = monto.split(".")
			parte_entera_2 = self.completar_campo_izquierda(partes_monto[0], '0', 14)
			parte_decimal_2 = str(partes_monto[1])
			if len(parte_decimal_2) == 1:
				parte_decimal_2 = ""+parte_decimal_2 + "0"
			elif len(parte_decimal_2) == 0:
				parte_decimal_2 = "00"

			detalle_n1.append(parte_entera_2+"."+parte_decimal_2)
			if lineas_detalles:
				lineas_detalles = lineas_detalles+ '\r\n'+ ''.join(detalle_n1)
			else:
				lineas_detalles = lineas_detalles+ ''.join(detalle_n1)

			for rel in factura.reversal_move_id:
				detalle_n = []
				# 1
				detalle_n.append('3')
				# 2 (Tipo de Documento a pagar)
				detalle_n.append('N')
				# 3 (Nro. del Documento - 15)
				nro_doc = rel.l10n_latam_document_number
				detalle_n.append(self.completar_campo_izquierda(nro_doc, '0', 15))
				# 4 (Monto del Documento - 14 y 2 decimales)
				monto_nota = rel.monto_neto_pagar_base
				total_credito = total_credito + rel.monto_neto_pagar_base
				monto_nota = str(monto_nota)
				partes_monto_nota = monto_nota.split(".")
				parte_entera = self.completar_campo_izquierda(partes_monto_nota[0], '0', 14)
				parte_decimal = str(partes_monto_nota[1])
				if parte_decimal == "0":
					parte_decimal = "00"
				elif len(parte_decimal) == 1:
					parte_decimal = ""+parte_decimal + "0"
				elif len(parte_decimal) == 0:
					parte_decimal = "00"
				detalle_n.append(parte_entera+"."+parte_decimal)
				linea_n = ''.join(detalle_n)
				lineas_detalles = lineas_detalles+'\r\n'+ linea_n

		###### Fin de detalles
		
		# 11 (Monto del Abono)
		monto_total = total_facturas - total_credito
		monto_total = round(monto_total, 2)
		monto_total = str(monto_total)
		partes_monto_total = monto_total.split(".")
		parte_entera_t = self.completar_campo_izquierda(partes_monto_total[0], '0', 14)
		parte_decimal_t = str(partes_monto_total[1])
		if len(parte_decimal_t) == 1:
			parte_decimal_t = ""+parte_decimal_t + "0"
		elif len(parte_decimal_t) == 0:
			parte_decimal_t = "00"

		monto_completo_str = ""+parte_entera_t+"."+parte_decimal_t+""
		linea_cabecera.append(monto_completo_str)
		linea_n1 = ''.join(linea_cabecera)
		# 12 (Tipo de Moneda de Abono)
		moneda = ''
		#if factura.currency_id.name == 'USD':
		if self.cuenta_cargo.currency_id.name == 'USD':
			moneda = 'D'
		else:
			moneda = 'S'
		#linea_cabecera.append(moneda)
		#linea_n1 = ''.join(linea_cabecera)
		linea_n1 = linea_n1 + "" + moneda

		linea_respuesta = linea_n1+'\r\n' + lineas_detalles

		if tipo_cuenta == "B":
			#monto_abono = monto_abono + CDbl(Mid(NroCuentaAbono, 11, Len(NroCuentaAbono) - 10))
			string_nro_abono = numero_cuenta[11: len(numero_cuenta) - 10]
			monto_abono = monto_abono + float(string_nro_abono)
		else:
			#monto_abono = monto_abono + CDbl(Mid(NroCuentaAbono, 4, Len(NroCuentaAbono) - 3))
			string_nro_abono = numero_cuenta[4: len(numero_cuenta) - 3]
			monto_abono = monto_abono + float(string_nro_abono)

		return [linea_respuesta, monto_abono]

	def obtener_cuenta_entidad(self, entidad):
		bancos = entidad.bank_ids
		for banco in bancos:
			return banco

		return False

	def completar_campo_izquierda(self, contenido, campo_completar, cantidad):
		dato = ""
		cant_en_contenido = len(contenido)
		cant_resta = cantidad - cant_en_contenido
		for ind in range(0, cant_resta):
			dato = campo_completar+""+dato

		dato = dato + contenido
		return dato

	def completar_campo_derecha(self, contenido, campo_completar, cantidad):
		dato = ""
		cant_en_contenido = len(contenido)
		cant_resta = cantidad - cant_en_contenido
		for ind in range(0, cant_resta):
			dato = dato+""+campo_completar

		dato = contenido + dato
		return dato


	def unlink(self):
		for reg in self:
			for pago in reg.pago_ids:
				pago.write({
					'telecredito_id': False
				})

			for factura in reg.factura_ids:
				factura.write({
					'telecredito_id': False
				})
		return super(Telecredito, self).unlink()

	def registrar_pago(self):
		pmt_wizard = self.env['account.payment.register.temp'].with_context(active_model='account.move', active_ids=self.factura_ids.ids).create({
			'payment_date': self.fecha,
			'journal_id': self.cuenta_cargo.id,
			'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
		})
		pmt_wizard._create_payments()
		self.state = 'confirmado'