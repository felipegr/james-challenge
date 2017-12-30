import hashlib
import math
import simplejson as json
import unittest
import transaction
import webtest

from pyramid import testing
from pyramid.threadlocal import get_current_registry

from james.models import Loan


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
        
        self.assertEquals(math.floor(loan.installment * 100) / 100, 85.6)
    
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
