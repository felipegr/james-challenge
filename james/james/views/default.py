import ast

import colander
from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import IntegrityError

from james.models import Loan
from james.views.validators import NumberGreaterThanZero


class CreateLoanSchema(colander.MappingSchema):
    amount = colander.SchemaNode(colander.Float(),
        validator=NumberGreaterThanZero(), type='float')
    term = colander.SchemaNode(colander.Integer(),
        validator=NumberGreaterThanZero(), type='int')
    rate = colander.SchemaNode(colander.Float(),
        validator=NumberGreaterThanZero(), type='float')
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
