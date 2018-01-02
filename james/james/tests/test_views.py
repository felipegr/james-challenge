from datetime import datetime
import hashlib
import math
import simplejson as json
import unittest
import transaction
import webtest

from pyramid import testing
from pyramid.threadlocal import get_current_registry

from james.models import Loan, Payment


class BaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from james import main
        from james.models import get_tm_session
        from james.models.meta import Base

        settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'auth.secret': 'seekrit',
            'api.key': 'key'
        }
        app = main({}, **settings)
        cls.testapp = webtest.TestApp(app)

        session_factory = app.registry['dbsession_factory']
        cls.engine = session_factory.kw['bind']
        Base.metadata.create_all(bind=cls.engine)
        
        cls.session = get_tm_session(session_factory, transaction.manager)

    @classmethod
    def tearDownClass(cls):
        from james.models.meta import Base
        Base.metadata.drop_all(bind=cls.engine)
    
    def setUp(self):
        self.headers = {'authorization': hashlib.sha256('key').hexdigest()}


class TestAddLoan(BaseTest):
    
    def test_success(self):
        data = {'amount': 1000, 'term': 12, 'rate': 0.05,
                'date': '2017-08-05 02:18Z'}
        
        res = self.testapp.post('/loans', json.dumps(data),
                                headers=self.headers)
        
        loan = self.session.query(Loan).filter_by(
            loan_id=res.json_body['loan_id']).one()
        
        self.assertEquals(loan.amount, 1000)
        self.assertEquals(loan.term, 12)
        self.assertEquals(loan.rate, 0.05)
        self.assertEquals(loan.date, datetime(2017, 8, 5, 2, 18))
        self.assertEquals(loan.installment, 85.6)
    
    def test_unauthorized(self):
        data = {'amount': 1000, 'term': 12, 'rate': 0.05,
                'date': '2017-08-05 02:18Z'}
        
        res = self.testapp.post('/loans', json.dumps(data), status=403)
    
    def test_missing_json(self):
        res = self.testapp.post('/loans', headers=self.headers, status=400)
        
        self.assertEquals(res.json_body['error'], 'Invalid JSON.')

    def test_missing_required_fields(self):
        data = {}
        
        res = self.testapp.post('/loans', json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['date'], 'Required')
        self.assertEquals(res.json_body['amount'], 'Required')
        self.assertEquals(res.json_body['term'], 'Required')
        self.assertEquals(res.json_body['rate'], 'Required')

    def test_incorrect_formats(self):
        data = {'amount': 'text', 'term': 'text', 'rate': 'text',
                'date': '05/08/2017 02:18Z'}
        
        res = self.testapp.post('/loans', json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['date'], 'Invalid date')
        self.assertEquals(res.json_body['amount'], '"text" is not a number')
        self.assertEquals(res.json_body['term'], '"text" is not a number')
        self.assertEquals(res.json_body['rate'], '"text" is not a number')

    def test_incorrect_values(self):
        data = {'amount': -87, 'term': -9, 'rate': -0.98,
                'date': '2017-08-05 02:18Z'}
        
        res = self.testapp.post('/loans', json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['amount'],
                          'Value must be greater than zero')
        self.assertEquals(res.json_body['term'],
                          'Value must be greater than zero')
        self.assertEquals(res.json_body['rate'],
                          'Value must be greater than zero')


class TestAddPayment(BaseTest):
    
    def setUp(self):
        self.headers = {'authorization': hashlib.sha256('key').hexdigest()}
        
        data = {'amount': 1000, 'term': 12, 'rate': 0.05,
                'date': '2017-08-05 02:18Z'}
        
        res = self.testapp.post('/loans', json.dumps(data),
                                headers=self.headers)
        
        self.loan = self.session.query(Loan).filter_by(
            loan_id=res.json_body['loan_id']).one()
        
        self.assertEquals(self.loan.installment, 85.6)
    
    def tearDown(self):
        self.session.query(Payment).delete()
        self.session.query(Loan).delete()
        self.session.flush()
    
    def test_success(self):
        data = {'payment': 'made', 'date': '2017-08-05 02:18Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers)
        
        payment_1 = self.session.query(Payment).filter_by(loan=self.loan).one()
        
        self.assertEquals(payment_1.loan_id, self.loan.id)
        self.assertEquals(payment_1.payment, 'made')
        self.assertEquals(payment_1.date, datetime(2017, 8, 5, 2, 18))
        self.assertEquals(payment_1.amount, 85.6)
        
        data = {'payment': 'missed', 'date': '2017-09-05 02:18Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers)
        
        payment_2 = self.session.query(Payment).filter(
            Payment.id != payment_1.id).one()
        
        self.assertEquals(payment_2.loan_id, self.loan.id)
        self.assertEquals(payment_2.payment, 'missed')
        self.assertEquals(payment_2.date, datetime(2017, 9, 5, 2, 18))
        self.assertEquals(payment_2.amount, 85.6)
    
    def test_loan_not_found(self):
        data = {'payment': 'made', 'date': '2017-08-05 02:18Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/unknown/payments', json.dumps(data),
                                headers=self.headers, status=404)
        
    def test_unauthorized(self):
        data = {'payment': 'made', 'date': '2017-08-05 02:18Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), status=403)
    
    def test_missing_json(self):
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                headers=self.headers, status=400)
        
        self.assertEquals(res.json_body['error'], 'Invalid JSON.')

    def test_missing_required_fields(self):
        data = {}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['payment'], 'Required')
        self.assertEquals(res.json_body['date'], 'Required')
        self.assertEquals(res.json_body['amount'], 'Required')

    def test_invalid_date(self):
        data = {'payment': 'made', 'date': '2017-07-15 03:29Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['error'],
            'Invalid payment date, must be later than or equal to loan date.')

    def test_invalid_amount(self):
        data = {'payment': 'made', 'date': '2017-08-05 03:29Z', 'amount': 90.87}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers,
                                status=400)
        
        self.assertEquals(res.json_body['error'],
                          'Invalid amount, must be $85.6.')
    
    def test_duplicated_payment(self):
        data = {'payment': 'made', 'date': '2017-08-05 02:18Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers)
        
        payment_1 = self.session.query(Payment).filter_by(loan=self.loan).one()
        
        self.assertEquals(payment_1.loan_id, self.loan.id)
        self.assertEquals(payment_1.payment, 'made')
        self.assertEquals(payment_1.date, datetime(2017, 8, 5, 2, 18))
        self.assertEquals(payment_1.amount, 85.6)
        
        data = {'payment': 'made', 'date': '2017-08-05 22:34Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers,
                                status=409)
        
        self.assertEquals(res.json_body['error'], 'Duplicated payment.')
        
        data = {'payment': 'missed', 'date': '2017-08-05 04:00Z', 'amount': 85.6}
        
        res = self.testapp.post('/loans/{}/payments'.format(self.loan.loan_id),
                                json.dumps(data), headers=self.headers,
                                status=409)
        
        self.assertEquals(res.json_body['error'], 'Duplicated payment.')
