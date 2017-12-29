from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String
)

from .meta import Base


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
