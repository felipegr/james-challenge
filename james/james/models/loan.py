from datetime import datetime
import math
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    func,
    Integer,
    Numeric,
    String
)

from .meta import Base
from .payment import Payment


class InvalidDate(Exception):
    pass


class Loan(Base):
    __tablename__ = 'loan'
    
    id = Column(Integer, primary_key=True)
    loan_id = Column(String(32), index=True, nullable=False,
                     default=uuid.uuid4().hex)
    amount = Column(Numeric(19, 10, asdecimal=False), nullable=False)
    term = Column(Integer, nullable=False)
    rate = Column(Numeric(19, 10, asdecimal=False), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    installment = Column(Numeric(19, 10, asdecimal=False), nullable=False)
    
    def set_installment_value(self):
        installment = ((self.rate / self.term) + (self.rate / self.term) / \
                       ((1 + (self.rate / self.term)) ** self.term - 1)) \
                      * self.amount
        self.installment = math.floor(installment * 100) / 100

    def calculate_balance(self, date):
        if date < self.date.date():
            raise InvalidDate
        
        total = self.installment * self.term
        
        if not self.payments.first():
            return round(total, 2)
        
        query = self.payments
        query = query.filter(func.date(Payment.date) <= date,
                             Payment.payment == 'made')
        paid_installments = query.count() * self.installment

        return round(total - paid_installments, 2)
