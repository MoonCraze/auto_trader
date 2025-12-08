"""
FastAPI server for historical trade data and analytics endpoints.
Provides REST API for querying user trades, portfolio history, and analytics.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db, Trade, Position, PortfolioSnapshot, User
from pydantic import BaseModel
import json

app = FastAPI(title="Trading Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class TradeResponse(BaseModel):
    id: int
    token_symbol: str
    token_address: str
    status: str
    entry_time: datetime
    entry_price: float
    quantity: float
    sol_invested: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    sol_returned: Optional[float]
    pnl_sol: Optional[float]
    pnl_percent: Optional[float]
    exit_reason: Optional[str]
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    token_symbol: str
    token_address: str
    tokens: float
    cost_basis: float
    last_updated: datetime
    
    class Config:
        from_attributes = True

class TokenAnalytics(BaseModel):
    token_symbol: str
    token_address: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_invested: float
    total_returned: float
    net_pnl: float
    avg_pnl_percent: float
    best_trade_pnl: float
    worst_trade_pnl: float

class OverallAnalytics(BaseModel):
    total_trades: int
    active_trades: int
    finished_trades: int
    total_wins: int
    total_losses: int
    win_rate: float
    total_volume_sol: float
    total_pnl_sol: float
    avg_trade_size_sol: float
    avg_pnl_per_trade: float
    largest_win: float
    largest_loss: float
    unique_tokens_traded: int

# Endpoints

@app.get("/")
def root():
    return {"message": "Trading Bot API", "version": "1.0.0"}

@app.post("/api/register")
def register_user(db: Session = Depends(get_db)):
    """Register a new synthetic wallet"""
    from auth import register_synthetic_wallet
    result = register_synthetic_wallet(db)
    return result

@app.get("/api/user/{wallet_address}")
def get_user(wallet_address: str, db: Session = Depends(get_db)):
    """Get user information"""
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "wallet_address": user.wallet_address,
        "created_at": user.created_at,
        "initial_sol_balance": user.initial_sol_balance
    }

@app.get("/api/trades/{wallet_address}", response_model=List[TradeResponse])
def get_trades(
    wallet_address: str,
    status: Optional[str] = Query(None, description="Filter by status: active, finished, failed"),
    token_address: Optional[str] = Query(None, description="Filter by token address"),
    limit: int = Query(100, le=500, description="Max results to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get trade history for a wallet with optional filters"""
    query = db.query(Trade).filter(Trade.wallet_address == wallet_address)
    
    if status:
        query = query.filter(Trade.status == status)
    if token_address:
        query = query.filter(Trade.token_address == token_address)
    
    trades = query.order_by(desc(Trade.entry_time)).limit(limit).offset(offset).all()
    return trades

@app.get("/api/trades/{wallet_address}/{trade_id}", response_model=TradeResponse)
def get_trade_detail(wallet_address: str, trade_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific trade"""
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.wallet_address == wallet_address
    ).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade

@app.get("/api/positions/{wallet_address}", response_model=List[PositionResponse])
def get_positions(wallet_address: str, db: Session = Depends(get_db)):
    """Get current open positions for a wallet"""
    positions = db.query(Position).filter(
        Position.wallet_address == wallet_address
    ).all()
    return positions

@app.get("/api/portfolio/history/{wallet_address}")
def get_portfolio_history(
    wallet_address: str,
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get portfolio value history over time"""
    since = datetime.utcnow() - timedelta(days=days)
    
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.wallet_address == wallet_address,
        PortfolioSnapshot.timestamp >= since
    ).order_by(PortfolioSnapshot.timestamp).all()
    
    return [{
        "timestamp": s.timestamp,
        "sol_balance": s.sol_balance,
        "total_value": s.total_value,
        "overall_pnl": s.overall_pnl
    } for s in snapshots]

@app.get("/api/analytics/{wallet_address}/overall", response_model=OverallAnalytics)
def get_overall_analytics(wallet_address: str, db: Session = Depends(get_db)):
    """Get overall trading analytics for a wallet"""
    # Get all finished trades
    finished_trades = db.query(Trade).filter(
        Trade.wallet_address == wallet_address,
        Trade.status == 'finished'
    ).all()
    
    active_trades_count = db.query(func.count(Trade.id)).filter(
        Trade.wallet_address == wallet_address,
        Trade.status == 'active'
    ).scalar()
    
    total_trades = len(finished_trades)
    wins = sum(1 for t in finished_trades if t.pnl_sol and t.pnl_sol > 0)
    losses = sum(1 for t in finished_trades if t.pnl_sol and t.pnl_sol <= 0)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    total_volume = sum(t.sol_invested for t in finished_trades)
    total_pnl = sum(t.pnl_sol for t in finished_trades if t.pnl_sol)
    avg_trade_size = total_volume / total_trades if total_trades > 0 else 0.0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0.0
    
    pnls = [t.pnl_sol for t in finished_trades if t.pnl_sol is not None]
    largest_win = max(pnls) if pnls else 0.0
    largest_loss = min(pnls) if pnls else 0.0
    
    unique_tokens = db.query(func.count(func.distinct(Trade.token_address))).filter(
        Trade.wallet_address == wallet_address
    ).scalar()
    
    return OverallAnalytics(
        total_trades=total_trades + active_trades_count,
        active_trades=active_trades_count,
        finished_trades=total_trades,
        total_wins=wins,
        total_losses=losses,
        win_rate=win_rate,
        total_volume_sol=total_volume,
        total_pnl_sol=total_pnl,
        avg_trade_size_sol=avg_trade_size,
        avg_pnl_per_trade=avg_pnl,
        largest_win=largest_win,
        largest_loss=largest_loss,
        unique_tokens_traded=unique_tokens
    )

@app.get("/api/analytics/{wallet_address}/by-token", response_model=List[TokenAnalytics])
def get_token_analytics(wallet_address: str, db: Session = Depends(get_db)):
    """Get per-token analytics for a wallet"""
    # Query finished trades grouped by token
    trades_by_token = db.query(Trade).filter(
        Trade.wallet_address == wallet_address,
        Trade.status == 'finished'
    ).all()
    
    # Group trades by token
    token_map = {}
    for trade in trades_by_token:
        if trade.token_address not in token_map:
            token_map[trade.token_address] = {
                'symbol': trade.token_symbol,
                'trades': []
            }
        token_map[trade.token_address]['trades'].append(trade)
    
    # Calculate analytics per token
    analytics = []
    for token_addr, data in token_map.items():
        trades = data['trades']
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.pnl_sol and t.pnl_sol > 0)
        losses = sum(1 for t in trades if t.pnl_sol and t.pnl_sol <= 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        
        total_invested = sum(t.sol_invested for t in trades)
        total_returned = sum(t.sol_returned for t in trades if t.sol_returned)
        net_pnl = sum(t.pnl_sol for t in trades if t.pnl_sol)
        
        pnl_percents = [t.pnl_percent for t in trades if t.pnl_percent is not None]
        avg_pnl_percent = sum(pnl_percents) / len(pnl_percents) if pnl_percents else 0.0
        
        pnls = [t.pnl_sol for t in trades if t.pnl_sol is not None]
        best_trade = max(pnls) if pnls else 0.0
        worst_trade = min(pnls) if pnls else 0.0
        
        analytics.append(TokenAnalytics(
            token_symbol=data['symbol'],
            token_address=token_addr,
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_invested=total_invested,
            total_returned=total_returned,
            net_pnl=net_pnl,
            avg_pnl_percent=avg_pnl_percent,
            best_trade_pnl=best_trade,
            worst_trade_pnl=worst_trade
        ))
    
    # Sort by net P&L descending
    analytics.sort(key=lambda x: x.net_pnl, reverse=True)
    return analytics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
