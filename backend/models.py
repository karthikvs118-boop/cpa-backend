from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.database import Base


# 👤 USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    balance = Column(Float, default=0.0)


# 💰 TRANSACTION MODEL
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)

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


# 🔥 CLICK MODEL (CORE OF TRACKING SYSTEM)
class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # 🔗 linked to user
    sub_id = Column(String, unique=True, index=True)  # unique tracking ID