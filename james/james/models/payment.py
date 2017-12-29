from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String
)
from sqlalchemy.orm import backref, relationship

from .meta import Base


class Payment(Base):
    __tablename__ = 'payment'
    
    id = Column(Integer, primary_key=True)
    loan_id = Column(Integer, ForeignKey('loan.id'), nullable=False, index=True)
    loan = relationship('Loan', backref=backref('payments', lazy='dynamic'),
                        foreign_keys=[loan_id])
    payment = Column(String(6), index=True, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    amount = Column(Numeric(19, 10, asdecimal=False), nullable=False)
