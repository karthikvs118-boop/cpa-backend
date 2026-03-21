from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from backend.database import Base
from datetime import datetime


# 👤 USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    balance = Column(Float, default=0.0)

    # 🔥 ANTI-FRAUD FIELDS
    ip_address = Column(String)  # track registration IP
    is_blocked = Column(Integer, default=0)  # 0 = active, 1 = blocked


# 💰 TRANSACTION MODEL
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)

    type = Column(String)  # credit / debit
    tx_id = Column(String, unique=True, index=True)

    # 🔥 IMPORTANT FIELDS
    type = Column(String)  # credit / debit
    tx_id = Column(String, unique=True, index=True)  # CPA conversion ID


# 💸 WITHDRAWAL MODEL
class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending / approved / rejected


# 🔥 CLICK MODEL (CORE + ANTI-FRAUD)
class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # 🔗 linked to user
    sub_id = Column(String, unique=True, index=True)  # unique tracking ID

    # 🔥 NEW ANTI-FRAUD FIELDS
    ip_address = Column(String)  # track click source
    created_at = Column(DateTime, default=datetime.utcnow)  # time tracking