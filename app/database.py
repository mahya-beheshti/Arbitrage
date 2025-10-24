import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./arbitrage.db")

# Handle PostgreSQL SSL if deployed on managed cloud DB (optional)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # check_same_thread is required for SQLite if using it outside the request thread
    connect_args = {"check_same_thread": False}

# Note: PostgreSQL URLs usually start with 'postgresql://' or 'postgres://'
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    pair = Column(String, index=True)
    buy_exchange = Column(String)
    sell_exchange = Column(String)
    sell_price = Column(Float)
    buy_price = Column(Float)
    diffrence = Column(Float)
    difference_percent = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    print("Database initialization...")
    print("WARNING: Dropping existing 'opportunities' table to apply schema change...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database ready.")
