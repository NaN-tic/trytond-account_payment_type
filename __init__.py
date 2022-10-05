# This file is part of account_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import move
from . import payment_type
from . import party
from . import invoice
from . import commission
from . import work
from . import sale


def register():
    Pool.register(
        payment_type.PaymentType,
        move.Move,
        move.Line,
        party.PartyAccountPaymentType,
        party.Party,
        invoice.Invoice,
        sale.Sale,
        module='account_payment_type', type_='model')
    Pool.register(
        commission.Commission,
        depends=['commission'],
        module='account_payment_type', type_='model')
    Pool.register(
        work.Work,
        depends=['project_invoice'],
        module='account_payment_type', type_='model')
