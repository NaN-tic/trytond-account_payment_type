# This file is part of account_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contain
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.modules.company.model import CompanyValueMixin
from trytond.transaction import Transaction

__all__ = ['PartyAccountPaymentType', 'Party']
customer_payment_type = fields.Many2One(
    'account.payment.type', 'Customer Payment type', domain=[
        ('kind', 'in', ['both', 'receivable']),
        ],
    help='Payment type of the customer.')
supplier_payment_type = fields.Many2One(
    'account.payment.type', string='Supplier Payment type', domain=[
        ('kind', 'in', ['both', 'payable']),
        ],
    help='Payment type of the supplier.')


class PartyAccountPaymentType(CompanyValueMixin, ModelSQL):
    'Party Account Payment Type'
    __name__ = 'party.account.payment.type'

    party = fields.Many2One('party.party', 'Party', ondelete='CASCADE',
        context={
            'company': Eval('company', -1),
        }, depends=['company'])
    customer_payment_type = customer_payment_type
    supplier_payment_type = supplier_payment_type


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    customer_payment_type = fields.MultiValue(customer_payment_type)
    supplier_payment_type = fields.MultiValue(supplier_payment_type)
    payment_types = fields.One2Many('party.account.payment.type', 'party',
        "Payment Types")

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.customer_payment_type.searcher = 'search_payment_type'
        cls.supplier_payment_type.searcher = 'search_payment_type'
        cls.payment_direct_debit.states = {
            'invisible': True,
        }

    @classmethod
    def search_payment_type(cls, name, clause):
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if not user.company:
            return []
        company_id = user.company.id

        field = clause[0]
        return [
            ('payment_types.%s' % field,) + tuple(clause[1:]),
            ('payment_types.company', '=', company_id)
            ]

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in ['customer_payment_type', 'supplier_payment_type']:
            return pool.get('party.account.payment.type')
        return super(Party, cls).multivalue_model(field)
