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
                        self._use_fallback_data()
        except Exception as e:
            print(f"An error occurred while fetching token metadata: {e}")
            self._use_fallback_data()
            
    def _use_fallback_data(self):
        """Use hardcoded fallback data when online fetch fails"""
        print("Using fallback token metadata...")
        self.token_map = {
            "8eye7ykjbjfcucrv3d3tgsd7f2ngujackvsf9ka8efwv": "goldcoin",
            "c3xe6hm8obq9ynkndpwzkysbt1pdnk2mi2to8bhykwx3": "Uni",
            "emelmjivmebilddtqzkp63mfue1u55ycyr4kkwkxk7gd": "fraudcoin",
            "dctvr8kcsr3da4fqxbpdheh87rw7y2t34u8yafww2scp": "MeowChi",
            "5bns2je5vrmvtyqa7x8psyfarja8plfybla5pjgkuyz9": "XAU",
            "hnxndek9suxvn12urquccxc267bwm1n472dhcvjmj35": "LION",
            "384jaovaa3qvwdu9e9axjdyh5v1zlfpgjqcwzxewlnq7": "POLYTREND"
        }
        print(f"Loaded {len(self.token_map)} fallback tokens.")

    def get_symbol(self, address: str) -> str:
        """Returns the symbol for a given address, or a truncated address if not found."""
        return self.token_map.get(address, f"{address[:4]}...{address[-4:]}")