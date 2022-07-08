# This file is part of account_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Bool, Eval, Not
from trytond.modules.account_payment_type.payment_type import KINDS

__all__ = ['Invoice']
ZERO = Decimal('0.0')


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'
    payment_type_kind = fields.Function(fields.Selection(KINDS,
            'Kind of payment type',
            states={
                'invisible': True,
                },
            ),
        'on_change_with_payment_type_kind')
    payment_type = fields.Many2One('account.payment.type', 'Payment Type',
        domain=[
            ('kind', 'in', ['both', Eval('payment_type_kind')]),
            ],
        states={
            'readonly': Not(Bool(Eval('state').in_(['draft', 'validated']))),
            },
        depends=['payment_type_kind', 'state'])

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # allow process or paid invoices when is posted
        cls._check_modify_exclude.add('payment_type')
        cls.payment_direct_debit.states = {
            'invisible': True,
        }

    @fields.depends('type', 'untaxed_amount', 'lines')
    def on_change_with_payment_type_kind(self, name=None):
        if self.untaxed_amount:
            if self.type == 'out':
                if self.untaxed_amount >= ZERO:
                    return 'receivable'
                else:
                    return 'payable'
            elif self.type == 'in':
                if self.untaxed_amount >= ZERO:
                    return 'payable'
                else:
                    return 'receivable'
        return 'receivable' if self.type == 'out' else 'payable'

    @fields.depends('party', 'company', 'type', 'untaxed_amount', 'lines')
    def on_change_with_payment_type(self, name=None):
        if (hasattr(self, 'payment_type') and self.payment_type
                and self.payment_type.kind == 'both'):
            return self.payment_type.id

        kind = self.on_change_with_payment_type_kind()
        if (hasattr(self, 'payment_type') and self.payment_type
                and self.payment_type.kind == kind):
            return self.payment_type.id

        if not self.untaxed_amount:
            return (self.payment_type.id
                if (hasattr(self, 'payment_type') and self.payment_type)
                else None)

        for party in [
                self.party,
                self.company.party if self.company else None]:
            if not party:
                continue

            if self.type == 'out':
                if kind == 'receivable':
                    name = 'customer_payment_type'
                else:
                    name = 'supplier_payment_type'
            elif self.type == 'in':
                if kind == 'payable':
                    name = 'supplier_payment_type'
                else:
                    name = 'customer_payment_type'

            payment_type = getattr(party, name)
            if payment_type:
                return payment_type.id
        return None

    def _get_move_line(self, date, amount):
        line = super(Invoice, self)._get_move_line(date, amount)
        if self.payment_type:
            line.payment_type = self.payment_type
        return line
