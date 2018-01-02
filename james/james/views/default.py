import ast

import colander
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from james.models import Loan, Payment
from james.models.loan import InvalidDate
from james.views.validators import NumberGreaterThanZero


class CreateLoanSchema(colander.MappingSchema):
    amount = colander.SchemaNode(colander.Float(),
        validator=NumberGreaterThanZero(), type='float')
    term = colander.SchemaNode(colander.Integer(),
        validator=NumberGreaterThanZero(), type='int')
    rate = colander.SchemaNode(colander.Float(),
        validator=NumberGreaterThanZero(), type='float')
    date = colander.SchemaNode(colander.DateTime(), type='datetime')


class CreatePaymentSchema(colander.MappingSchema):
    payment = colander.SchemaNode(colander.String(), type='str',
        validator=colander.OneOf(['made', 'missed']))
    date = colander.SchemaNode(colander.DateTime(), type='datetime')
    amount = colander.SchemaNode(colander.Float(),
        validator=NumberGreaterThanZero(), type='float')


class BalanceSchema(colander.MappingSchema):
    date = colander.SchemaNode(colander.DateTime(), type='datetime')


@view_config(route_name='add_loan', request_method='POST', renderer='json',
             permission='edit')
def add_loan(request):
    try:
        items = CreateLoanSchema().deserialize(request.json_body)
    except ValueError:
        request.response.status = 400
        return {'error': 'Invalid JSON.'}
    except colander.Invalid as e:
        request.response.status = 400
        return ast.literal_eval(e.__str__())
    
    loan = Loan(amount=items['amount'], term=items['term'], rate=items['rate'],
                date=items['date'])
    loan.set_installment_value()
    
    request.dbsession.add(loan)
    request.dbsession.flush()
    
    return {'loan_id': loan.loan_id, 'installment': loan.installment}


@view_config(route_name='add_payment', request_method='POST', renderer='json',
             permission='edit')
def add_payment(request):
    loan_id = request.matchdict['loan_id']
    
    loan = request.dbsession.query(Loan).filter_by(loan_id=loan_id).first()
    
    if not loan:
        raise HTTPNotFound('Loan not found')
    
    try:
        items = CreatePaymentSchema().deserialize(request.json_body)
    except ValueError:
        request.response.status = 400
        return {'error': 'Invalid JSON.'}
    except colander.Invalid as e:
        request.response.status = 400
        return ast.literal_eval(e.__str__())

    if items['date'].date() < loan.date.date():
        request.response.status = 400
        return {'error': 'Invalid payment date, must be later than or equal to' +
            ' {}.'.format(loan.date.date())}
    
    if items['amount'] != loan.installment:
        request.response.status = 400
        return {'error': 'Invalid amount, must be ${}.'.format(loan.installment)}
    
    if request.dbsession.query(Payment).filter(
        Payment.loan == loan,
        func.extract('year', Payment.date) == items['date'].year,
        func.extract('month', Payment.date) == items['date'].month
        ).first():
        request.response.status = 409
        return {'error': 'Duplicated payment.'}
    
    payment = Payment(loan=loan, payment=items['payment'], date=items['date'],
                      amount=items['amount'])
    
    request.dbsession.add(payment)
    request.dbsession.flush()
    
    return {'success': 'Payment added.'}


@view_config(route_name='balance', request_method='POST', renderer='json',
             permission='edit')
def balance(request):
    loan_id = request.matchdict['loan_id']
    
    loan = request.dbsession.query(Loan).filter_by(loan_id=loan_id).first()
    
    if not loan:
        raise HTTPNotFound('Loan not found')
    
    try:
        items = BalanceSchema().deserialize(request.json_body)
    except ValueError:
        request.response.status = 400
        return {'error': 'Invalid JSON.'}
    except colander.Invalid as e:
        request.response.status = 400
        return ast.literal_eval(e.__str__())

    try:
        return {'balance': loan.calculate_balance(items['date'].date())}
    except InvalidDate:
        request.response.status = 400
        return {'error': 'Invalid date, must be later than or equal to {}.'. \
            format(loan.date.date())}
