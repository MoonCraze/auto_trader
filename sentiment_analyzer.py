import aiohttp
import asyncio


SENTIMENT_ENDPOINT_URL = "https://ominous-giggle-wrjg64446pxq39rxv-8000.app.github.dev/coin-sentiment"
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 5

async def check_sentiment(token_address: str, symbol: str) -> dict | None:
    """
    Queries the sentiment analysis endpoint with a retry mechanism for API failures.
    It will IMMEDIATELY fail a token if the API returns 0 total mentions.

    Returns:
        A dictionary like {'score': 75, 'mentions': 50} on success, or None on failure.
    """
    params = {'coin': token_address, 'max_results': 300}
    
    for attempt in range(MAX_RETRIES):
        print(f"[{symbol}] Checking sentiment (Attempt {attempt + 1}/{MAX_RETRIES})...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SENTIMENT_ENDPOINT_URL, params=params, timeout=60) as response:
                    if response.status == 200:
                        data = await response.json()
                        total_mentions = data.get('total_mentions', 0)

                        # <<< THE DEFINITIVE FIX IS HERE ---
                        # If the API works but finds no data, this is an immediate failure. No retry.
                        if total_mentions == 0:
                            print(f"[{symbol}] Sentiment check found 0 mentions. Discarding signal immediately.")
                            return None # Return None to indicate failure.

                        # If we have mentions, return the full data payload.
                        # The calling function will decide if the score is high enough.
                        print(f"[{symbol}] Sentiment check successful. Score: {data.get('positive_pct', 0)}%, Mentions: {total_mentions}")
                        return {
                            "score": data.get('positive_pct', 0),
                            "mentions": total_mentions
                        }
                    else:
                        # This is a real API error (e.g., 500, 503). We SHOULD retry this.
                        print(f"[{symbol}] Sentiment check failed with status code: {response.status}. Retrying...")
                        response.raise_for_status() # This will trigger the except block.

        except Exception as e:
            # This block now only catches genuine connection/API errors.
            print(f"[{symbol}] An API or connection error occurred: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                print(f"[{symbol}] Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print(f"[{symbol}] Max retries reached for API error. Discarding signal.")
                return None

    # This is reached if all retries fail.
    return None