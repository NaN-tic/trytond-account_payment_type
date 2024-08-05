import datetime
import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import create_chart, get_accounts
from trytond.modules.account_invoice.tests.tools import create_payment_term
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

        # Install project_invoice
        config = activate_modules(['account_payment_type', 'project_invoice'])

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        config._context = User.get_preferences(True, config.context)

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create payment type
        PaymentType = Model.get('account.payment.type')
        receivable = PaymentType(name='Receivable', kind='receivable')
        receivable.save()
        payable = PaymentType(name='Payable', kind='payable')
        payable.save()

        # Create customer
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.customer_payment_term = payment_term
        customer.customer_payment_type = receivable
        customer.supplier_payment_type = payable
        customer.save()

        # Create employee
        Employee = Model.get('company.employee')
        employee = Employee()
        party = Party(name='Employee')
        party.save()
        employee.party = party
        employee.company = company
        employee.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = accounts['expense']
        account_category.account_revenue = accounts['revenue']
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        hour, = ProductUom.find([('name', '=', 'Hour')])
        Product = Model.get('product.product')
        ProductTemplate = Model.get('product.template')
        product = Product()
        template = ProductTemplate()
        template.name = 'Service'
        template.default_uom = hour
        template.type = 'service'
        template.list_price = Decimal('20')
        template.account_category = account_category
        template.save()
        product.template = template
        product.save()

        # Get status
        WorkStatus = Model.get('project.work.status')
        done, = WorkStatus.find([('name', '=', "Done")])

        # Create a Project
        ProjectWork = Model.get('project.work')
        TimesheetWork = Model.get('timesheet.work')
        project = ProjectWork()
        project.name = 'Test effort'
        work = TimesheetWork()
        work.name = 'Test effort'
        work.save()
        project.type = 'project'
        project.party = customer
        project.project_invoice_method = 'effort'
        project.product = product
        project.effort_duration = datetime.timedelta(hours=1)
        task = ProjectWork()
        task.name = 'Task 1'
        work = TimesheetWork()
        work.name = 'Task 1'
        work.save()
        task.type = 'task'
        task.product = product
        task.party = customer
        task.effort_duration = datetime.timedelta(hours=5)
        project.children.append(task)
        project.save()
        task, = project.children

        # Check project duration
        project.reload()
        self.assertEqual(project.invoiced_amount, Decimal('0'))

        # Do 1 task
        task.status = done
        task.save()

        # Invoice project
        project.click('invoice')
        task.reload()
        self.assertEqual(task.invoice_line.invoice.payment_type, receivable)
