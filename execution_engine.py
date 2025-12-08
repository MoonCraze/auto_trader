from database import Trade
from datetime import datetime
import json

class ExecutionEngine:
    def __init__(self, portfolio_manager, current_trade_id=None):
        self.portfolio_manager = portfolio_manager
        self.current_trade_id = current_trade_id  # Track active trade

    def execute_buy(self, token_info, sol_to_invest, current_price, strategy_params=None, sentiment_data=None):
        """Execute buy order and create Trade record in database"""
        if current_price <= 0:
            return 0
        
        token_address = token_info['address']
        token_symbol = token_info.get('symbol', token_address[:8])
        tokens_received = sol_to_invest / current_price
        
        success = self.portfolio_manager.record_buy(
            token_symbol=token_address,
            sol_spent=sol_to_invest,
            tokens_received=tokens_received,
            price=current_price
        )
        
        if not success:
            return 0
        
        # Create Trade record in database if wallet_address exists
        if self.portfolio_manager.wallet_address and self.portfolio_manager.db_session:
            trade = Trade(
                wallet_address=self.portfolio_manager.wallet_address,
                token_address=token_address,
                token_symbol=token_symbol,
                status='active',
                entry_time=datetime.utcnow(),
                entry_price=current_price,
                quantity=tokens_received,
                sol_invested=sol_to_invest,
                stop_loss_price=strategy_params.get('stop_loss_price') if strategy_params else None,
                take_profit_tiers=json.dumps(strategy_params.get('take_profit_tiers')) if strategy_params and 'take_profit_tiers' in strategy_params else None,
                highest_price_seen=current_price,
                initial_sentiment_score=sentiment_data.get('score') if sentiment_data else None,
                initial_mention_count=sentiment_data.get('mentions') if sentiment_data else None
            )
            self.portfolio_manager.db_session.add(trade)
            self.portfolio_manager.db_session.commit()
            self.portfolio_manager.db_session.refresh(trade)
            self.current_trade_id = trade.id
            print(f"✅ Created Trade #{trade.id} in database")
        
        return tokens_received

    def execute_sell(self, token_info, tokens_to_sell, current_price, exit_reason='manual'):
        """Execute sell order and update Trade record in database"""
        if current_price <= 0:
            return 0
        
        token_address = token_info['address']
        sol_received = tokens_to_sell * current_price
        
        success = self.portfolio_manager.record_sell(
            token_symbol=token_address,
            tokens_sold=tokens_to_sell,
            sol_received=sol_received,
            price=current_price
        )
        
        if not success:
            return 0
        
        # Update Trade record in database if exists
        if self.current_trade_id and self.portfolio_manager.wallet_address and self.portfolio_manager.db_session:
            trade = self.portfolio_manager.db_session.query(Trade).filter(
                Trade.id == self.current_trade_id
            ).first()
            
            if trade:
                # Check if position is fully closed
                position_closed = token_address not in self.portfolio_manager.positions or \
                                self.portfolio_manager.positions[token_address]['tokens'] < 1e-9
                
                if position_closed:
                    trade.status = 'finished'
                    trade.exit_time = datetime.utcnow()
                    trade.exit_price = current_price
                    trade.sol_returned = sol_received if not trade.sol_returned else trade.sol_returned + sol_received
                    trade.pnl_sol = trade.sol_returned - trade.sol_invested
                    trade.pnl_percent = ((trade.sol_returned / trade.sol_invested) - 1) * 100 if trade.sol_invested > 0 else 0
                    trade.exit_reason = exit_reason
                    print(f"✅ Closed Trade #{trade.id} | P&L: {trade.pnl_sol:+.4f} SOL ({trade.pnl_percent:+.2f}%)")
                else:
                    # Partial sell - update sol_returned
                    trade.sol_returned = sol_received if not trade.sol_returned else trade.sol_returned + sol_received
                    print(f"📊 Partial sell for Trade #{trade.id} | Received: {sol_received:.4f} SOL")
                
                self.portfolio_manager.db_session.commit()
        
        return sol_received