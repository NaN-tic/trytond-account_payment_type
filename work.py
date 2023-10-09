# This file is part of account_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta


class Work(metaclass=PoolMeta):
    __name__ = 'project.work'

    def _get_invoice(self):
        Invoice = Pool().get('account.invoice')

        invoice = super(Work, self)._get_invoice()

        customer_payment_type = invoice.party.customer_payment_type
        if customer_payment_type:
            invoice.payment_type = customer_payment_type
            if hasattr(Invoice, 'bank_account') and invoice.payment_type:
                invoice.on_change_payment_type()

        return invoice
