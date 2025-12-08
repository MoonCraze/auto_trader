"""
Database models and setup for multi-user trading bot.
Tracks users, trades, positions, and portfolio snapshots.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class User(Base):
    """User/Wallet entity for synthetic wallet authentication"""
    __tablename__ = 'users'
    
    wallet_address = Column(String(100), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    initial_sol_balance = Column(Float, nullable=False)
    
    # Relationships
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan")

class Trade(Base):
    """Individual trade record with full entry/exit details"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(100), ForeignKey('users.wallet_address'), nullable=False, index=True)
    
    # Token details
    token_address = Column(String(100), nullable=False, index=True)
    token_symbol = Column(String(50), nullable=False)
    
    # Trade lifecycle
    status = Column(String(20), nullable=False, default='active')  # 'active', 'finished', 'failed'
    
    # Entry details
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    sol_invested = Column(Float, nullable=False)
    
    # Exit details (null for active trades)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    sol_returned = Column(Float, nullable=True)
    
    # P&L calculation
    pnl_sol = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    
    # Strategy parameters
    stop_loss_price = Column(Float, nullable=True)
    take_profit_tiers = Column(Text, nullable=True)  # JSON string
    highest_price_seen = Column(Float, nullable=True)
    
    # Sentiment data
    initial_sentiment_score = Column(Float, nullable=True)
    initial_mention_count = Column(Integer, nullable=True)
    
    # Exit reason
    exit_reason = Column(String(100), nullable=True)  # 'take_profit', 'stop_loss', 'manual', 'trailing_stop'
    
    # Relationships
    user = relationship("User", back_populates="trades")

class Position(Base):
    """Current open positions per user per token"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(100), ForeignKey('users.wallet_address'), nullable=False, index=True)
    token_address = Column(String(100), nullable=False, index=True)
    token_symbol = Column(String(50), nullable=False)
    
    tokens = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="positions")

class PortfolioSnapshot(Base):
    """Periodic snapshots of portfolio value for historical tracking"""
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(100), ForeignKey('users.wallet_address'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    sol_balance = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    overall_pnl = Column(Float, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_snapshots")

# Database setup
engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
