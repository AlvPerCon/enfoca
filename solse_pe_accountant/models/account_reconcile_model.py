from re import match
from odoo import models, fields, api, _
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from collections import defaultdict

# Se modifica para poder realizar la conciliacion bancaria usando el numero de operación
class accountReconcileModel(models.Model):
	_inherit = 'account.reconcile.model'

	match_text_location_transaction_number = fields.Boolean(
		default=False,
		help="Search in the Statement's Reference to find the Invoice/Payment's reference",
	)

	def _get_invoice_matching_query(self, st_lines_with_partner, excluded_ids):
		''' Returns the query applying the current invoice_matching reconciliation
		model to the provided statement lines.

		:param st_lines_with_partner: A list of tuples (statement_line, partner),
									  associating each statement line to treate with
									  the corresponding partner, given by the partner map
		:param excluded_ids:    Account.move.lines to exclude.
		:return:                (query, params)
		'''
		self.ensure_one()
		if self.rule_type != 'invoice_matching':
			raise UserError(
				_('Programmation Error: Can\'t call _get_invoice_matching_query() for different rules than \'invoice_matching\''))

		unaccent = get_unaccent_wrapper(self._cr)

		# N.B: 'communication_flag' is there to distinguish invoice matching through the number/reference
		# (higher priority) from invoice matching using the partner (lower priority).
		query = r'''
		SELECT
			st_line.id                          AS id,
			aml.id                              AS aml_id,
			aml.currency_id                     AS aml_currency_id,
			aml.date_maturity                   AS aml_date_maturity,
			aml.amount_residual                 AS aml_amount_residual,
			aml.amount_residual_currency        AS aml_amount_residual_currency,
			''' + self._get_select_communication_flag() + r''' AS communication_flag,
			''' + self._get_select_payment_reference_flag() + r''' AS payment_reference_flag,
			''' + self._get_select_transaction_number_flag() + r''' AS transaction_number_flag
		FROM account_bank_statement_line st_line
		JOIN account_move st_line_move          ON st_line_move.id = st_line.move_id
		JOIN res_company company                ON company.id = st_line_move.company_id
		, account_move_line aml
		LEFT JOIN account_move move             ON move.id = aml.move_id AND move.state = 'posted'
		LEFT JOIN account_account account       ON account.id = aml.account_id
		LEFT JOIN res_partner aml_partner       ON aml.partner_id = aml_partner.id
		LEFT JOIN account_payment payment       ON payment.move_id = move.id
		WHERE
			aml.company_id = st_line_move.company_id
			AND move.state = 'posted'
			AND account.reconcile IS TRUE
			AND aml.reconciled IS FALSE
		'''

		# Add conditions to handle each of the statement lines we want to match
		st_lines_queries = []
		for st_line, partner in st_lines_with_partner:
			# In case we don't have any partner for this line, we try assigning one with the rule mapping
			if st_line.amount > 0:
				st_line_subquery = r"aml.balance > 0"
			else:
				st_line_subquery = r"aml.balance < 0"

			# ADDED
			if self.match_text_location_transaction_number:
				st_line_subquery += r" AND aml.transaction_number = '%s'" % (
					st_line.transaction_number)

			if self.match_same_currency:
				st_line_subquery += r" AND COALESCE(aml.currency_id, company.currency_id) = %s" % (
					st_line.foreign_currency_id.id or st_line.move_id.currency_id.id)

			if partner:
				st_line_subquery += r" AND aml.partner_id = %s" % partner.id
			elif not self.match_text_location_transaction_number:
				st_line_subquery += r"""
					AND
					(
						substring(REGEXP_REPLACE(st_line.payment_ref, '[^0-9\s]', '', 'g'), '\S(?:.*\S)*') != ''
						AND
						(
							(""" + self._get_select_communication_flag() + """)
							OR
							(""" + self._get_select_payment_reference_flag() + """)
						)
					)
					OR
					(
						/* We also match statement lines without partners with amls
						whose partner's name's parts (splitting on space) are all present
						within the payment_ref, in any order, with any characters between them. */

						aml_partner.name IS NOT NULL
						AND """ + unaccent("st_line.payment_ref") + r""" ~* ('^' || (
							SELECT string_agg(concat('(?=.*\m', chunk[1], '\M)'), '')
							  FROM regexp_matches(""" + unaccent("aml_partner.name") + r""", '\w{3,}', 'g') AS chunk
						))
					)
				"""

			st_lines_queries.append(
				r"st_line.id = %s AND (%s)" % (st_line.id, st_line_subquery))

		query += r" AND (%s) " % " OR ".join(st_lines_queries)

		params = {}

		# If this reconciliation model defines a past_months_limit, we add a condition
		# to the query to only search on move lines that are younger than this limit.
		if self.past_months_limit:
			date_limit = fields.Date.context_today(
				self) - relativedelta(months=self.past_months_limit)
			query += "AND aml.date >= %(aml_date_limit)s"
			params['aml_date_limit'] = date_limit

		# Filter out excluded account.move.line.
		if excluded_ids:
			query += 'AND aml.id NOT IN %(excluded_aml_ids)s'
			params['excluded_aml_ids'] = tuple(excluded_ids)

		if self.matching_order == 'new_first':
			query += ' ORDER BY aml_date_maturity DESC, aml_id DESC'
		else:
			query += ' ORDER BY aml_date_maturity ASC, aml_id ASC'

		return query, params
	
	def _get_select_transaction_number_flag(self):
		if self.match_text_location_transaction_number:
			return "TRUE"
		else:
			return "FALSE"
	
	def _sort_reconciliation_candidates_by_priority(self, candidates, already_proposed_aml_ids, already_reconciled_aml_ids):
		""" Sorts the provided candidates and returns a mapping of candidates by
		priority (1 being the highest).

		The priorities are defined as follows:

		1: payment_reference_flag is true,  so the move's payment_reference
		   field matches the statement line's.

		2: Same as 1, but the candidates have already been proposed for a previous statement line

		3: communication_flag is true, so either the move's ref, move's name or
		   aml's name match the statement line's payment reference.

		4: Same as 3, but the candidates have already been proposed for a previous statement line

		5: candidates proposed by the query, but no match with the statement
		   line's payment ref could be found.

		6: Same as 5, but the candidates have already been proposed for a previous statement line
		"""
		candidates_by_priority = defaultdict(lambda: [])

		for candidate in filter(lambda x: x['aml_id'] not in already_reconciled_aml_ids, candidates):

			if candidate['payment_reference_flag'] or candidate['transaction_number_flag']:
				priority = 1
			elif candidate['communication_flag']:
				priority = 3
			else:
				priority = 5

			if candidate['aml_id'] in already_proposed_aml_ids:
				# So, priorities 2, 4 and 6 are created here
				priority += 1

			candidates_by_priority[priority].append(candidate)

		return candidates_by_priority