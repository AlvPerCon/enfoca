# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import json
_logging = logging.getLogger(__name__)

INCLUIDOS = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']

class AccountMoveSunat(models.Model):
	_inherit = 'account.move'

	@api.model
	def _get_default_fecha_factura(self):
		move_type = self._context.get('default_move_type', 'entry')
		if move_type == 'in_invoice':
			return fields.Date.context_today(self)
		else:
			return False

	invoice_date = fields.Date(string='Invoice/Bill Date', default=_get_default_fecha_factura, readonly=True, index=True, copy=False, states={'draft': [('readonly', False)]})
	fecha_tipo_cambio = fields.Date("Fecha tipo de cambio", compute="_compute_fecha_tipo_cambio", help="Fecha que se toma para el tipo de cambio.\nPara compras toma la fecha de factura y para los demás movimientos la fecha contable")

	@api.depends('move_type', 'date', 'invoice_date')
	def _compute_fecha_tipo_cambio(self):
		for reg in self:
			fecha = reg.invoice_date
			if reg.state in ['posted', 'cancel', 'annull']:
				reg.fecha_tipo_cambio = reg.date
				continue
			if reg.move_type == 'in_invoice': # Facturas proveedor
				fecha = reg.invoice_date
			elif reg.move_type == 'in_refund': # Notas de credito proveedor
				fecha = reg.reversed_entry_id.invoice_date
			elif reg.move_type == 'out_refund': # Notas de credito cliente
				fecha = reg.reversed_entry_id.invoice_date
			elif reg.move_type == 'out_invoice' and reg.es_x_apertura: # Facturas de cliente
				fecha = reg.invoice_date
			else:
				fecha = reg.date

			reg.fecha_tipo_cambio = fecha
			#reg.fecha_tipo_cambio = reg.date
			#reg._onchange_currency()
			#reg._onchange_recompute_dynamic_lines()

	@api.onchange('invoice_date', 'highest_name', 'company_id')
	def _onchange_invoice_date(self):
		_logging.info("======================= _onchange_invoice_date")
		self._compute_fecha_tipo_cambio()
		if self.invoice_date:
			if not self.invoice_payment_term_id and (not self.invoice_date_due or self.invoice_date_due < self.invoice_date):
				self.invoice_date_due = self.invoice_date

			has_tax = bool(self.line_ids.tax_ids or self.line_ids.tax_tag_ids)
			accounting_date = self._get_accounting_date(self.invoice_date, has_tax)
			if accounting_date != self.date:
				fecha_apertura = self.fecha_apertura or accounting_date
				self.date = fecha_apertura if self.es_x_apertura else accounting_date
				self._onchange_currency()
			else:
				self._onchange_recompute_dynamic_lines()

	def _recompute_tax_lines(self, recompute_tax_base_amount=False):
		_logging.info("======================= _recompute_tax_lines")
		""" Compute the dynamic tax lines of the journal entry.

		:param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
		"""
		self.ensure_one()
		in_draft_mode = self != self._origin

		def _serialize_tax_grouping_key(grouping_dict):
			''' Serialize the dictionary values to be used in the taxes_map.
			:param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
			:return: A string representing the values.
			'''
			return '-'.join(str(v) for v in grouping_dict.values())

		def _compute_base_line_taxes(base_line):
			''' Compute taxes amounts both in company currency / foreign currency as the ratio between
			amount_currency & balance could not be the same as the expected currency rate.
			The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
			:param base_line:   The account.move.line owning the taxes.
			:return:            The result of the compute_all method.
			'''
			move = base_line.move_id

			if move.is_invoice(include_receipts=True):
				handle_price_include = True
				sign = -1 if move.is_inbound() else 1
				quantity = base_line.quantity
				is_refund = move.move_type in ('out_refund', 'in_refund')
				price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
			else:
				handle_price_include = False
				quantity = 1.0
				tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
				is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
				price_unit_wo_discount = base_line.amount_currency

			balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
				price_unit_wo_discount,
				currency=base_line.currency_id,
				quantity=quantity,
				product=base_line.product_id,
				partner=base_line.partner_id,
				is_refund=is_refund,
				handle_price_include=handle_price_include,
			)

			if move.move_type == 'entry':
				repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
				repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
				tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
				if tags_need_inversion:
					balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
					for tax_res in balance_taxes_res['taxes']:
						tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

			return balance_taxes_res

		taxes_map = {}

		# ==== Add tax lines ====
		to_remove = self.env['account.move.line']
		for line in self.line_ids.filtered('tax_repartition_line_id'):
			grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
			grouping_key = _serialize_tax_grouping_key(grouping_dict)
			if grouping_key in taxes_map:
				# A line with the same key does already exist, we only need one
				# to modify it; we have to drop this one.
				to_remove += line
			else:
				taxes_map[grouping_key] = {
					'tax_line': line,
					'amount': 0.0,
					'tax_base_amount': 0.0,
					'grouping_dict': False,
				}
		if not recompute_tax_base_amount:
			self.line_ids -= to_remove

		# ==== Mount base lines ====
		for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
			# Don't call compute_all if there is no tax.
			if not line.tax_ids:
				if not recompute_tax_base_amount:
					line.tax_tag_ids = [(5, 0, 0)]
				continue

			compute_all_vals = _compute_base_line_taxes(line)

			# Assign tags on base line
			if not recompute_tax_base_amount:
				line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

			tax_exigible = True
			for tax_vals in compute_all_vals['taxes']:
				grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
				grouping_key = _serialize_tax_grouping_key(grouping_dict)

				tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

				if tax.tax_exigibility == 'on_payment':
					tax_exigible = False

				taxes_map_entry = taxes_map.setdefault(grouping_key, {
					'tax_line': None,
					'amount': 0.0,
					'tax_base_amount': 0.0,
					'grouping_dict': False,
				})
				taxes_map_entry['amount'] += tax_vals['amount']
				taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
				taxes_map_entry['grouping_dict'] = grouping_dict
			if not recompute_tax_base_amount:
				line.tax_exigible = tax_exigible

		# ==== Pre-process taxes_map ====
		taxes_map = self._preprocess_taxes_map(taxes_map)

		# ==== Process taxes_map ====
		for taxes_map_entry in taxes_map.values():
			# The tax line is no longer used in any base lines, drop it.
			if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
				if not recompute_tax_base_amount:
					self.line_ids -= taxes_map_entry['tax_line']
				continue

			currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

			# Don't create tax lines with zero balance.
			if currency.is_zero(taxes_map_entry['amount']):
				if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
					self.line_ids -= taxes_map_entry['tax_line']
				continue

			# tax_base_amount field is expressed using the company currency.
			fecha_tipo_cambio = self.date if self.move_type not in INCLUIDOS else self.fecha_tipo_cambio
			tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, fecha_tipo_cambio)

			# Recompute only the tax_base_amount.
			if recompute_tax_base_amount:
				if taxes_map_entry['tax_line']:
					taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
				continue

			balance = currency._convert(
				taxes_map_entry['amount'],
				self.company_currency_id,
				self.company_id,
				fecha_tipo_cambio,
			)
			to_write_on_line = {
				'amount_currency': taxes_map_entry['amount'],
				'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
				'debit': balance > 0.0 and balance or 0.0,
				'credit': balance < 0.0 and -balance or 0.0,
				'tax_base_amount': tax_base_amount,
			}

			if taxes_map_entry['tax_line']:
				# Update an existing tax line.
				taxes_map_entry['tax_line'].update(to_write_on_line)
			else:
				# Create a new tax line.
				create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
				tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
				tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
				taxes_map_entry['tax_line'] = create_method({
					**to_write_on_line,
					'name': tax.name,
					'move_id': self.id,
					'company_id': line.company_id.id,
					'company_currency_id': line.company_currency_id.id,
					'tax_base_amount': tax_base_amount,
					'exclude_from_invoice_tab': True,
					'tax_exigible': tax.tax_exigibility == 'on_invoice',
					**taxes_map_entry['grouping_dict'],
				})

			if in_draft_mode:
				taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


	def _recompute_cash_rounding_lines(self):
		_logging.info("======================= _recompute_cash_rounding_lines")
		''' Handle the cash rounding feature on invoices.

		In some countries, the smallest coins do not exist. For example, in Switzerland, there is no coin for 0.01 CHF.
		For this reason, if invoices are paid in cash, you have to round their total amount to the smallest coin that
		exists in the currency. For the CHF, the smallest coin is 0.05 CHF.

		There are two strategies for the rounding:

		1) Add a line on the invoice for the rounding: The cash rounding line is added as a new invoice line.
		2) Add the rounding in the biggest tax amount: The cash rounding line is added as a new tax line on the tax
		having the biggest balance.
		'''
		self.ensure_one()
		in_draft_mode = self != self._origin

		def _compute_cash_rounding(self, total_amount_currency):
			''' Compute the amount differences due to the cash rounding.
			:param self:                    The current account.move record.
			:param total_amount_currency:   The invoice's total in invoice's currency.
			:return:                        The amount differences both in company's currency & invoice's currency.
			'''
			difference = self.invoice_cash_rounding_id.compute_difference(self.currency_id, total_amount_currency)
			if self.currency_id == self.company_id.currency_id:
				diff_amount_currency = diff_balance = difference
			else:
				diff_amount_currency = difference
				fecha_tipo_cambio = self.date if self.move_type not in INCLUIDOS else self.fecha_tipo_cambio
				diff_balance = self.currency_id._convert(diff_amount_currency, self.company_id.currency_id, self.company_id, fecha_tipo_cambio)
			return diff_balance, diff_amount_currency

		def _apply_cash_rounding(self, diff_balance, diff_amount_currency, cash_rounding_line):
			''' Apply the cash rounding.
			:param self:                    The current account.move record.
			:param diff_balance:            The computed balance to set on the new rounding line.
			:param diff_amount_currency:    The computed amount in invoice's currency to set on the new rounding line.
			:param cash_rounding_line:      The existing cash rounding line.
			:return:                        The newly created rounding line.
			'''
			rounding_line_vals = {
				'debit': diff_balance > 0.0 and diff_balance or 0.0,
				'credit': diff_balance < 0.0 and -diff_balance or 0.0,
				'quantity': 1.0,
				'amount_currency': diff_amount_currency,
				'partner_id': self.partner_id.id,
				'move_id': self.id,
				'currency_id': self.currency_id.id,
				'company_id': self.company_id.id,
				'company_currency_id': self.company_id.currency_id.id,
				'is_rounding_line': True,
				'sequence': 9999,
			}

			if self.invoice_cash_rounding_id.strategy == 'biggest_tax':
				biggest_tax_line = None
				for tax_line in self.line_ids.filtered('tax_repartition_line_id'):
					if not biggest_tax_line or tax_line.price_subtotal > biggest_tax_line.price_subtotal:
						biggest_tax_line = tax_line

				# No tax found.
				if not biggest_tax_line:
					return

				rounding_line_vals.update({
					'name': _('%s (rounding)', biggest_tax_line.name),
					'account_id': biggest_tax_line.account_id.id,
					'tax_repartition_line_id': biggest_tax_line.tax_repartition_line_id.id,
					'tax_tag_ids': [(6, 0, biggest_tax_line.tax_tag_ids.ids)],
					'tax_exigible': biggest_tax_line.tax_exigible,
					'exclude_from_invoice_tab': True,
				})

			elif self.invoice_cash_rounding_id.strategy == 'add_invoice_line':
				if diff_balance > 0.0 and self.invoice_cash_rounding_id.loss_account_id:
					account_id = self.invoice_cash_rounding_id.loss_account_id.id
				else:
					account_id = self.invoice_cash_rounding_id.profit_account_id.id
				rounding_line_vals.update({
					'name': self.invoice_cash_rounding_id.name,
					'account_id': account_id,
				})

			# Create or update the cash rounding line.
			if cash_rounding_line:
				cash_rounding_line.update({
					'amount_currency': rounding_line_vals['amount_currency'],
					'debit': rounding_line_vals['debit'],
					'credit': rounding_line_vals['credit'],
					'account_id': rounding_line_vals['account_id'],
				})
			else:
				create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
				cash_rounding_line = create_method(rounding_line_vals)

			if in_draft_mode:
				cash_rounding_line.update(cash_rounding_line._get_fields_onchange_balance(force_computation=True))

		existing_cash_rounding_line = self.line_ids.filtered(lambda line: line.is_rounding_line)

		# The cash rounding has been removed.
		if not self.invoice_cash_rounding_id:
			self.line_ids -= existing_cash_rounding_line
			return

		# The cash rounding strategy has changed.
		if self.invoice_cash_rounding_id and existing_cash_rounding_line:
			strategy = self.invoice_cash_rounding_id.strategy
			old_strategy = 'biggest_tax' if existing_cash_rounding_line.tax_line_id else 'add_invoice_line'
			if strategy != old_strategy:
				self.line_ids -= existing_cash_rounding_line
				existing_cash_rounding_line = self.env['account.move.line']

		others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
		others_lines -= existing_cash_rounding_line
		total_amount_currency = sum(others_lines.mapped('amount_currency'))

		diff_balance, diff_amount_currency = _compute_cash_rounding(self, total_amount_currency)

		# The invoice is already rounded.
		if self.currency_id.is_zero(diff_balance) and self.currency_id.is_zero(diff_amount_currency):
			self.line_ids -= existing_cash_rounding_line
			return

		_apply_cash_rounding(self, diff_balance, diff_amount_currency, existing_cash_rounding_line)

	def _inverse_amount_total(self):
		_logging.info("======================= _inverse_amount_total")
		for move in self:
			if len(move.line_ids) != 2 or move.is_invoice(include_receipts=True):
				continue

			to_write = []

			amount_currency = abs(move.amount_total)
			fecha_tipo_cambio = move.date if move.move_type not in INCLUIDOS else move.fecha_tipo_cambio
			balance = move.currency_id._convert(amount_currency, move.company_currency_id, move.company_id, fecha_tipo_cambio)

			for line in move.line_ids:
				if not line.currency_id.is_zero(balance - abs(line.balance)):
					to_write.append((1, line.id, {
						'debit': line.balance > 0.0 and balance or 0.0,
						'credit': line.balance < 0.0 and balance or 0.0,
						'amount_currency': line.balance > 0.0 and amount_currency or -amount_currency,
					}))

			move.write({'line_ids': to_write})

	def _compute_payments_widget_to_reconcile_info(self):
		_logging.info("======================= _compute_payments_widget_to_reconcile_info")
		for move in self:
			move.invoice_outstanding_credits_debits_widget = json.dumps(False)
			move.invoice_has_outstanding = False

			if move.state != 'posted' \
					or move.payment_state not in ('not_paid', 'partial') \
					or not move.is_invoice(include_receipts=True):
				continue

			pay_term_lines = move.line_ids\
				.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

			domain = [
				('account_id', 'in', pay_term_lines.account_id.ids),
				('parent_state', '=', 'posted'),
				('partner_id', '=', move.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]

			payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

			if move.is_inbound():
				domain.append(('balance', '<', 0.0))
				payments_widget_vals['title'] = _('Outstanding credits')
			else:
				domain.append(('balance', '>', 0.0))
				payments_widget_vals['title'] = _('Outstanding debits')

			for line in self.env['account.move.line'].search(domain):

				if line.currency_id == move.currency_id:
					# Same foreign currency.
					amount = abs(line.amount_residual_currency)
				else:
					# Different foreign currencies.
					fecha_tipo_cambio = line.date if move.move_type not in INCLUIDOS else move.fecha_tipo_cambio
					amount = move.company_currency_id._convert(
						abs(line.amount_residual),
						move.currency_id,
						move.company_id,
						fecha_tipo_cambio,
					)

				if move.currency_id.is_zero(amount):
					continue

				payments_widget_vals['content'].append({
					'journal_name': line.ref or line.move_id.name,
					'amount': amount,
					'currency': move.currency_id.symbol,
					'id': line.id,
					'move_id': line.move_id.id,
					'position': move.currency_id.position,
					'digits': [69, move.currency_id.decimal_places],
					'payment_date': fields.Date.to_string(line.date),
				})

			if not payments_widget_vals['content']:
				continue

			move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
			move.invoice_has_outstanding = True


class AccountMoveLineSunat(models.Model):
	_inherit = 'account.move.line'

	parent_move_type = fields.Selection(related='move_id.move_type', store=True, readonly=True)

	@api.onchange('currency_id')
	def _onchange_currency(self):
		_logging.info("======================= _onchange_currency")
		for line in self:
			company = line.move_id.company_id
			if line.move_id.is_invoice(include_receipts=True):
				line._onchange_price_subtotal()
			elif not line.move_id.reversed_entry_id:
				fecha_tipo_cambio = line.move_id.date if line.move_id.move_type not in INCLUIDOS else line.move_id.fecha_tipo_cambio
				balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, fecha_tipo_cambio)
				line.debit = balance if balance > 0.0 else 0.0
				line.credit = -balance if balance < 0.0 else 0.0


	@api.model
	def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
		_logging.info("======================= _get_fields_onchange_subtotal_model")
		''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
		in some business fields (affecting the 'price_subtotal' field).

		:param price_subtotal:  The untaxed amount.
		:param move_type:       The type of the move.
		:param currency:        The line's currency.
		:param company:         The move's company.
		:param date:            The move's date.
		:return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
		'''
		if move_type in self.move_id.get_outbound_types():
			sign = 1
		elif move_type in self.move_id.get_inbound_types():
			sign = -1
		else:
			sign = 1

		amount_currency = price_subtotal * sign
		fecha_tipo_cambio = date if self.move_id.move_type not in INCLUIDOS else self.move_id.fecha_tipo_cambio
		balance = currency._convert(amount_currency, company.currency_id, company, fecha_tipo_cambio)
		return {
			'amount_currency': amount_currency,
			'currency_id': currency.id,
			'debit': balance > 0.0 and balance or 0.0,
			'credit': balance < 0.0 and -balance or 0.0,
		}

	@api.onchange('amount_currency')
	def _onchange_amount_currency(self):
		_logging.info("======================= _onchange_amount_currency")
		for line in self:
			company = line.move_id.company_id
			fecha_tipo_cambio = line.move_id.date if line.move_id.move_type not in INCLUIDOS else line.move_id.fecha_tipo_cambio
			balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, fecha_tipo_cambio)
			line.debit = balance if balance > 0.0 else 0.0
			line.credit = -balance if balance < 0.0 else 0.0

			if not line.move_id.is_invoice(include_receipts=True):
				continue

			line.update(line._get_fields_onchange_balance())
			line.update(line._get_price_total_and_subtotal())

	def _prepare_reconciliation_partials(self):
		_logging.info("======================= _prepare_reconciliation_partials")
		''' Prepare the partials on the current journal items to perform the reconciliation.
		/!\ The order of records in self is important because the journal items will be reconciled using this order.

		:return: A recordset of account.partial.reconcile.
		'''
		def fix_remaining_cent(currency, abs_residual, partial_amount):
			if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
				return abs_residual
			else:
				return partial_amount

		debit_lines = iter(self.filtered(lambda line: line.balance > 0.0 or line.amount_currency > 0.0))
		credit_lines = iter(self.filtered(lambda line: line.balance < 0.0 or line.amount_currency < 0.0))
		debit_line = None
		credit_line = None

		debit_amount_residual = 0.0
		debit_amount_residual_currency = 0.0
		credit_amount_residual = 0.0
		credit_amount_residual_currency = 0.0
		debit_line_currency = None
		credit_line_currency = None

		partials_vals_list = []

		while True:

			# Move to the next available debit line.
			if not debit_line:
				debit_line = next(debit_lines, None)
				if not debit_line:
					break
				debit_amount_residual = debit_line.amount_residual

				if debit_line.currency_id:
					debit_amount_residual_currency = debit_line.amount_residual_currency
					debit_line_currency = debit_line.currency_id
				else:
					debit_amount_residual_currency = debit_amount_residual
					debit_line_currency = debit_line.company_currency_id

			# Move to the next available credit line.
			if not credit_line:
				credit_line = next(credit_lines, None)
				if not credit_line:
					break
				credit_amount_residual = credit_line.amount_residual

				if credit_line.currency_id:
					credit_amount_residual_currency = credit_line.amount_residual_currency
					credit_line_currency = credit_line.currency_id
				else:
					credit_amount_residual_currency = credit_amount_residual
					credit_line_currency = credit_line.company_currency_id

			min_amount_residual = min(debit_amount_residual, -credit_amount_residual)
			has_debit_residual_left = not debit_line.company_currency_id.is_zero(debit_amount_residual) and debit_amount_residual > 0.0
			has_credit_residual_left = not credit_line.company_currency_id.is_zero(credit_amount_residual) and credit_amount_residual < 0.0
			has_debit_residual_curr_left = not debit_line_currency.is_zero(debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
			has_credit_residual_curr_left = not credit_line_currency.is_zero(credit_amount_residual_currency) and credit_amount_residual_currency < 0.0

			if debit_line_currency == credit_line_currency:
				# Reconcile on the same currency.

				# The debit line is now fully reconciled because:
				# - either amount_residual & amount_residual_currency are at 0.
				# - either the credit_line is not an exchange difference one.
				if not has_debit_residual_curr_left and (has_credit_residual_curr_left or not has_debit_residual_left):
					debit_line = None
					continue

				# The credit line is now fully reconciled because:
				# - either amount_residual & amount_residual_currency are at 0.
				# - either the debit is not an exchange difference one.
				if not has_credit_residual_curr_left and (has_debit_residual_curr_left or not has_credit_residual_left):
					credit_line = None
					continue

				min_amount_residual_currency = min(debit_amount_residual_currency, -credit_amount_residual_currency)
				min_debit_amount_residual_currency = min_amount_residual_currency
				min_credit_amount_residual_currency = min_amount_residual_currency

			else:
				# Reconcile on the company's currency.

				# The debit line is now fully reconciled since amount_residual is 0.
				if not has_debit_residual_left:
					debit_line = None
					continue

				# The credit line is now fully reconciled since amount_residual is 0.
				if not has_credit_residual_left:
					credit_line = None
					continue

				fecha_tipo_cambio_credit = credit_line.date if credit_line.move_id.move_type not in INCLUIDOS else credit_line.move_id.fecha_tipo_cambio
				min_debit_amount_residual_currency = credit_line.company_currency_id._convert(
					min_amount_residual,
					debit_line.currency_id,
					credit_line.company_id,
					fecha_tipo_cambio_credit,
				)
				min_debit_amount_residual_currency = fix_remaining_cent(
					debit_line.currency_id,
					debit_amount_residual_currency,
					min_debit_amount_residual_currency,
				)

				fecha_tipo_cambio_debit = debit_line.date if debit_line.move_id.move_type not in INCLUIDOS else debit_line.move_id.fecha_tipo_cambio
				min_credit_amount_residual_currency = debit_line.company_currency_id._convert(
					min_amount_residual,
					credit_line.currency_id,
					debit_line.company_id,
					fecha_tipo_cambio_debit,
				)
				min_credit_amount_residual_currency = fix_remaining_cent(
					credit_line.currency_id,
					-credit_amount_residual_currency,
					min_credit_amount_residual_currency,
				)

			debit_amount_residual -= min_amount_residual
			debit_amount_residual_currency -= min_debit_amount_residual_currency
			credit_amount_residual += min_amount_residual
			credit_amount_residual_currency += min_credit_amount_residual_currency

			partials_vals_list.append({
				'amount': min_amount_residual,
				'debit_amount_currency': min_debit_amount_residual_currency,
				'credit_amount_currency': min_credit_amount_residual_currency,
				'debit_move_id': debit_line.id,
				'credit_move_id': credit_line.id,
			})

		return partials_vals_list