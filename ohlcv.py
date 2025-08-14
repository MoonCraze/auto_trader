from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize the browser
driver = Driver(uc=True, headless=True)  # uc=True for undetected mode
driver.get("https://dexscreener.com/solana/dysa4qao8mtfzjncqvr8zpjq27k5rizbvvfyxbfetenk")

# Wait for the transactions container to load
container = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'tbody[data-testid="virtuoso-item-list"]')
    )
)

# Track processed transactions using a set (using inner text as identifier)
processed_transactions = set()

try:
    while True:  # Continuous monitoring loop
        # Get current transaction rows within the container
        rows = container.find_elements(By.CSS_SELECTOR, "tr")
        
        for row in rows:
            # Use row text as unique identifier (modify if needed)
            row_text = row.text.strip()
            
            if row_text and row_text not in processed_transactions:
                print("New Transaction:", row_text)
                
                # Extract structured data here (example: split text)
                # Modify based on actual row structure
                # Example: cells = row.find_elements(By.TAG_NAME, "td")
                #          data = [cell.text for cell in cells]
                
                processed_transactions.add(row_text)  # Mark as processed
        
        # Short delay before next poll
        time.sleep(1)

except KeyboardInterrupt:
    print("Monitoring stopped by user")
finally:
    driver.quit()