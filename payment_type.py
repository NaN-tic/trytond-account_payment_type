# This file is part of account_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, DeactivableMixin, fields
from trytond.pyson import Eval, If
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['PaymentType']

KINDS = [
    ('both', 'Both'),
    ('payable', 'Payable'),
    ('receivable', 'Receivable'),
    ]


class PaymentType(DeactivableMixin, ModelSQL, ModelView):
    'Payment Type'
    __name__ = 'account.payment.type'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code')
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, readonly=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', 0)),
            ])
    note = fields.Text('Description', translate=True,
        help=('Description of the payment type that will be shown in '
            'descriptions'))
    kind = fields.Selection(KINDS, 'Kind', required=True,
        help='The kind of payment type.')

    @classmethod
    def __setup__(cls):
        super(PaymentType, cls).__setup__()
        cls._check_modify_fields = set(['kind'])
        cls._check_modify_related_models = set([
                ('account.move.line', 'payment_type'),
                ('account.invoice', 'payment_type'),
                ])

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def default_kind(cls):
        return 'both'

    def get_rec_name(self, name):
        if self.code:
            return '[' + self.code + '] ' + self.name
        else:
            return self.name

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        args = []
        for payment_types, values in zip(actions, actions):
            keys = set(values.keys()) & cls._check_modify_fields
            if keys:
                cls.check_modify_fields(payment_types, keys)
            args.extend((payment_types, values))
        super(PaymentType, cls).write(*args)

    @classmethod
    def check_modify_fields(cls, payment_types, fields):
        pool = Pool()
        IrModel = pool.get('ir.model')
        Field = pool.get('ir.model.field')
        payment_ids = [p.id for p in payment_types]
        for model_name, field_name in cls._check_modify_related_models:
            Model = pool.get(model_name)
            records = Model.search([(field_name, 'in', payment_ids)], limit=1)
            if records:
                record, = records
                model, = IrModel.search([('model', '=', model_name)])
                field, = Field.search([
                        ('model.model', '=', cls.__name__),
                        ('name', 'in', list(fields)),
                        ], limit=1)
                # Use payment from record to be coherent in error message
                payment_type = getattr(record, field_name)
                raise UserError(gettext(
                    'account_payment_type.modifiy_with_related_model',
                    name=record.rec_name,
                    model=model.name,
                    type=payment_type.rec_name,
                    field=field.field_description))
