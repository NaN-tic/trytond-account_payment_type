
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from decimal import Decimal

from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction

from trytond.modules.company.tests import (CompanyTestMixin, create_company,
    set_company)
from trytond.modules.account.tests import create_chart, get_fiscalyear
from trytond.modules.account_invoice.tests import set_invoice_sequences


class AccountPaymentTypeTestCase(CompanyTestMixin, ModuleTestCase):
    'Test AccountPaymentType module'
    module = 'account_payment_type'

    @with_transaction()
    def test_move_lines(self):
        'Test move lines'
        pool = Pool()
        Account = pool.get('account.account')
        FiscalYear = pool.get('account.fiscalyear')
        Journal = pool.get('account.journal')
        Move = pool.get('account.move')
        MoveLine = pool.get('account.move.line')
        PaymentType = pool.get('account.payment.type')

        company = create_company()
        with set_company(company):
            create_chart(company)
            fiscalyear = get_fiscalyear(company)
            set_invoice_sequences(fiscalyear)
            fiscalyear.save()
            FiscalYear.create_period([fiscalyear])
            period = fiscalyear.periods[0]

            journal_revenue, = Journal.search([
                    ('code', '=', 'REV'),
                    ])
            revenue, = Account.search([
                    ('type.revenue', '=', True),
                    ('closed', '=', False),
                    ], limit=1)
            receivable, = Account.search([
                    ('type.receivable', '=', True),
                    ('closed', '=', False),
                    ], limit=1)
            payable, = Account.search([
                    ('type.payable', '=', True),
                    ('closed', '=', False),
                    ], limit=1)
            payment_payable, = PaymentType.create([{
                    'name': 'Payment Payable',
                    'kind': 'payable',
                    'company': company.id,
                    }])
            payment_receivable, = PaymentType.create([{
                    'name': 'Payment Receivable',
                    'kind': 'receivable',
                    'company': company.id,
                    }])
            move, = Move.create([{
                    'period': period.id,
                    'journal': journal_revenue.id,
                    'date': period.start_date,
                    }])
            MoveLine.create([{
                    'move': move.id,
                    'account': revenue.id,
                    'debit': Decimal(30),
                    }])
            self.assertRaises(Exception, MoveLine.create, [{
                    'move': move.id,
                    'account': revenue.id,
                    'debit': Decimal(30),
                    'payment_type': payment_receivable,
                    }])
            # TODO Create move line payment + payment type payable


del ModuleTestCase
