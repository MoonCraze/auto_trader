import aiohttp

# Jupiter's Strict token list is a good source for this mapping
TOKEN_LIST_URL = "https://token.jup.ag/strict"

class TokenMetadata:
    def __init__(self):
        self.token_map = {}

    async def initialize(self):
        """Fetches the token list and builds the address-to-symbol map."""
        print("Fetching token metadata from Jupiter...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(TOKEN_LIST_URL) as response:
                    if response.status == 200:
                        tokens = await response.json()
                        # Create a dictionary for fast lookups: { "address": "symbol" }
                        self.token_map = {token['address']: token['symbol'] for token in tokens}
                        print(f"Successfully loaded metadata for {len(self.token_map)} tokens.")
                    else:
                        print(f"Failed to fetch token list. Status: {response.status}")
        except Exception as e:
            print(f"An error occurred while fetching token metadata: {e}")

    def get_symbol(self, address: str) -> str:
        """Returns the symbol for a given address, or a truncated address if not found."""
        return self.token_map.get(address, f"{address[:4]}...{address[-4:]}")