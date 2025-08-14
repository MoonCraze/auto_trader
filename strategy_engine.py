import config

class StrategyEngine:
    def __init__(self, token_info, entry_price, initial_token_quantity):
        self.token_address = token_info['address']
        self.token_symbol = token_info['symbol']
        self.entry_price = entry_price
        self.initial_token_quantity = initial_token_quantity
        
        self.highest_price_seen = entry_price
        self.take_profit_levels_hit = [False] * len(config.TAKE_PROFIT_TIERS)
        self.is_breakeven_stop = False
        self.stop_loss_price = self.entry_price * (1 - config.INITIAL_STOP_LOSS_PERCENT)
        
        print(f"[{self.token_symbol}] Strategy Initialized. Entry: {self.entry_price:.6f}, Stop-Loss: {self.stop_loss_price:.6f}")

    def check_for_trade_action(self, current_price):
        if current_price <= self.stop_loss_price:
            reason = "Breakeven stop" if self.is_breakeven_stop else "Initial stop-loss"
            return ('SELL', 1.0, f"{reason} triggered at {current_price:.6f}")

        for i, (profit_target, sell_portion) in enumerate(config.TAKE_PROFIT_TIERS):
            if not self.take_profit_levels_hit[i]:
                target_price = self.entry_price * (1 + profit_target)
                if current_price >= target_price:
                    self.take_profit_levels_hit[i] = True
                    if not self.is_breakeven_stop:
                        self.stop_loss_price = self.entry_price
                        self.is_breakeven_stop = True
                        print(f"[{self.token_symbol}] Stop-loss moved to breakeven: {self.entry_price:.6f}")
                    reason = f"Take-profit {i+1} ({profit_target*100}%) triggered at {current_price:.6f}"
                    return ('SELL', sell_portion, reason)

        if current_price > self.highest_price_seen:
            self.highest_price_seen = current_price
            if self.is_breakeven_stop:
                new_trailing_stop = self.highest_price_seen * (1 - config.TRAILING_STOP_LOSS_PERCENT)
                if new_trailing_stop > self.stop_loss_price:
                    self.stop_loss_price = new_trailing_stop
        
        return ('HOLD', None, None)