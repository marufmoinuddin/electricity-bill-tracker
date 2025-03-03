from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, ForeignKey
from .database import Base

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String, unique=True, index=True)
    customer_name = Column(String)
    account_id = Column(String)
    balance = Column(Numeric)
    status = Column(String)
    last_updated = Column(TIMESTAMP)

class UsageData(Base):
    __tablename__ = 'usage_data'
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    balance = Column(Numeric)
    recorded_at = Column(TIMESTAMP)