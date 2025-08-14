class ExecutionEngine:
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager

    def execute_buy(self, token_info, sol_to_invest, current_price):
        if current_price <= 0: return 0
        token_address = token_info['address']
        tokens_received = sol_to_invest / current_price
        success = self.portfolio_manager.record_buy(
            token_symbol=token_address,
            sol_spent=sol_to_invest,
            tokens_received=tokens_received,
            price=current_price
        )
        return tokens_received if success else 0

    def execute_sell(self, token_info, tokens_to_sell, current_price):
        if current_price <= 0: return 0
        token_address = token_info['address']
        sol_received = tokens_to_sell * current_price
        success = self.portfolio_manager.record_sell(
            token_symbol=token_address,
            tokens_sold=tokens_to_sell,
            sol_received=sol_received,
            price=current_price
        )
        return sol_received if success else 0