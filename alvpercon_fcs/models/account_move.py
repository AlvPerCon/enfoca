# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
	_inherit = 'account.move'

	tipo_pagoxctc = fields.Selection([('cajachica', 'Caja Chica'),('tarjetacredito', 'Tarjeta Crédito')],'Documento Proveniente de')
		
