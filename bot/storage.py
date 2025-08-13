"""SQLite storage using SQLAlchemy."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    portfolio_value = Column(Float)
    lp_notional = Column(Float)
    perp_notional = Column(Float)
    delta = Column(Float)
    funding_apr = Column(Float)
    atr = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True)
    side = Column(String)
    qty = Column(Float)
    price = Column(Float)
    fees = Column(Float)
    delta_before = Column(Float)
    delta_after = Column(Float)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MetricsDaily(Base):
    __tablename__ = "metrics_daily"

    date = Column(String, primary_key=True)
    pnl_lp_fees = Column(Float)
    pnl_perp = Column(Float)
    funding_cost = Column(Float)
    net_pnl = Column(Float)


def init_db(db_path: str = "sqlite:///bot.db"):
    engine = create_engine(db_path, future=True)
    Base.metadata.create_all(engine)
    return engine


Engine = init_db()
SessionLocal = sessionmaker(bind=Engine, autoflush=False, autocommit=False)


def get_session():
    """Yield a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
