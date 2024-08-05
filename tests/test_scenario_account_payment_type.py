import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install account_payment_type Module
        activate_modules('account_payment_type')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        account_receivable = accounts['receivable']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = accounts['expense']
        account_category.account_revenue = accounts['revenue']
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('50')
        template.account_category = account_category
        template.save()
        product.template = template
        product.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create payment type
        PaymentType = Model.get('account.payment.type')
        receivable = PaymentType(name='Receivable', kind='receivable')
        receivable.save()
        payable = PaymentType(name='Payable', kind='payable')
        payable.save()

        # Create party
        Party = Model.get('party.party')
        party = Party(name='Party')
        party.customer_payment_type = receivable
        party.supplier_payment_type = payable
        party.save()

        # Check invoice payment type is correctly assigned
        Invoice = Model.get('account.invoice')
        invoice = Invoice()
        invoice.party = party
        invoice.payment_term = payment_term
        invoice.payment_type
        line = invoice.lines.new()
        line.product = product
        line.quantity = 1
        line.unit_price = Decimal('50.0')
        self.assertEqual(invoice.untaxed_amount, Decimal('50.00'))
        self.assertEqual(invoice.payment_type, receivable)
        line = invoice.lines.new()
        line.product = product
        line.quantity = -1
        line.unit_price = Decimal('40.0')
        self.assertEqual(invoice.payment_type, receivable)

        # When its a return its ussed the supplier payment_kind
        line = invoice.lines.new()
        line.product = product
        line.quantity = -1
        line.unit_price = Decimal('40.0')
        self.assertEqual(invoice.untaxed_amount, Decimal('-30.00'))
        self.assertEqual(invoice.payment_type, payable)

        # And where clearing all the lines the recevaible payment type is used
        _ = invoice.lines.pop()
        _ = invoice.lines.pop()
        _ = invoice.lines.pop()
        self.assertEqual(invoice.payment_type, None)
        self.assertEqual(invoice.untaxed_amount, Decimal('0.00'))

        # Check invoice payment type is correctly assigned on supplier invoices
        invoice = Invoice(type='in')
        invoice.party = party
        invoice.payment_term = payment_term
        invoice.payment_type
        line = invoice.lines.new()
        line.product = product
        line.quantity = 1
        line.unit_price = Decimal('50.0')
        self.assertEqual(invoice.untaxed_amount, Decimal('50.00'))
        self.assertEqual(invoice.payment_type, payable)
        line = invoice.lines.new()
        line.product = product
        line.quantity = -1
        line.unit_price = Decimal('40.0')
        self.assertEqual(invoice.payment_type, payable)

        # When its a return its used the customer payment_type
        line = invoice.lines.new()
        line.product = product
        line.quantity = -1
        line.unit_price = Decimal('40.0')
        self.assertEqual(invoice.untaxed_amount, Decimal('-30.00'))
        self.assertEqual(invoice.payment_type, receivable)

        # And where clearing all the lines the payable payment type is used
        _ = invoice.lines.pop()
        _ = invoice.lines.pop()
        _ = invoice.lines.pop()
        self.assertEqual(invoice.payment_type, None)
        self.assertEqual(invoice.untaxed_amount, Decimal('0.00'))

        # Create both payment type
        both = PaymentType(name='Both', kind='both')
        both.save()

        # We can use both in negative and positive invoices
        invoice = Invoice()
        invoice.party = party
        invoice.payment_term = payment_term
        line = invoice.lines.new()
        line.product = product
        line.quantity = 1
        line.unit_price = Decimal('50.0')
        invoice.payment_type = both
        self.assertEqual(invoice.untaxed_amount, Decimal('50.00'))
        invoice.save()
        self.assertEqual(invoice.payment_type, both)
        invoice = Invoice()
        invoice.party = party
        invoice.payment_term = payment_term
        line = invoice.lines.new()
        line.product = product
        line.quantity = -1
        line.unit_price = Decimal('40.0')
        invoice.payment_type = both
        invoice.save()
        self.assertEqual(invoice.payment_type, both)

        # Post an invoice with payment type
        invoice = Invoice()
        invoice.party = party
        invoice.payment_term = payment_term
        line = invoice.lines.new()
        line.product = product
        line.quantity = 1
        line.unit_price = Decimal('50.0')
        invoice.payment_type = receivable
        self.assertEqual(invoice.untaxed_amount, Decimal('50.00'))
        invoice.save()
        invoice.click('post')
        line1, _, _ = invoice.move.lines
        self.assertEqual(line1.payment_type, receivable)
        self.assertEqual(line1.account, account_receivable)
