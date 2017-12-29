from datetime import datetime
import unittest
import transaction

from pyramid import testing
from sqlalchemy.exc import IntegrityError

from james.models import Loan, Payment


class BaseTest(unittest.TestCase):

    def setUp(self):
        from ..models import get_tm_session
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:'
        })
        self.config.include('..models')
        self.config.include('..routes')

        session_factory = self.config.registry['dbsession_factory']
        self.session = get_tm_session(session_factory, transaction.manager)

        self.init_database()

    def init_database(self):
        from ..models.meta import Base
        session_factory = self.config.registry['dbsession_factory']
        engine = session_factory.kw['bind']
        Base.metadata.create_all(engine)

    def tearDown(self):
        testing.tearDown()
        transaction.abort()


class TestLoan(BaseTest):

    def test_create_success(self):
        loan = Loan(amount=100.10, term=12, rate=0.87, date=datetime.now(),
                    installment=78.90)
        self.session.add(loan)
        self.session.flush()

        self.assertIsNotNone(loan.loan_id)
    
    def test_missing_fields(self):
        with self.assertRaises(IntegrityError):
            loan = Loan(term=12, rate=0.87, date=datetime.now(), installment=78.90)
            self.session.add(loan)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            loan = Loan(amount=100.10, rate=0.87, date=datetime.now(), installment=78.90)
            self.session.add(loan)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            loan = Loan(amount=204.50, term=14, date=datetime.now(), installment=78.90)
            self.session.add(loan)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            loan = Loan(amount=204.50, term=14, rate=1.76, installment=78.90)
            self.session.add(loan)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            loan = Loan(amount=204.50, term=14, rate=9.8, date=datetime.now())
            self.session.add(loan)
            self.session.flush()
        self.session.rollback()


class TestPayment(BaseTest):

    def test_create_success(self):
        loan = Loan(amount=100.10, term=12, rate=0.87, date=datetime.now(),
                    installment=78.90)
        payment = Payment(loan=loan, payment='payment', date=datetime.now(),
                          amount=100.10)
        self.session.add_all([loan, payment])
        self.session.flush()

        self.assertEquals(loan.id, payment.loan_id)
    
    def test_missing_fields(self):
        loan = Loan(amount=100.10, term=12, rate=0.87, date=datetime.now(),
                    installment=78.90)
        self.session.add(loan)
        self.session.flush()
        
        with self.assertRaises(IntegrityError):
            payment = Payment(payment='payment', date=datetime.now(),
                              amount=100.10)
            self.session.add(payment)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            payment = Payment(loan=loan, date=datetime.now(), amount=100.10)
            self.session.add(payment)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            payment = Payment(loan=loan, payment='payment', amount=100.10)
            self.session.add(payment)
            self.session.flush()
        self.session.rollback()
        
        with self.assertRaises(IntegrityError):
            payment = Payment(loan=loan, payment='payment', date=datetime.now())
            self.session.add(payment)
            self.session.flush()
        self.session.rollback()
