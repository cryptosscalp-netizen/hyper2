# agentThreshold.py
import time
from playwright.sync_api import sync_playwright
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

EMAIL_SENDER = "cryptosscalp@gmail.com"
EMAIL_PASSWORD = "gfke olcu ulud zpnh"
EMAIL_RECEIVER = "25harshitgarg12345@gmail.com"

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Navigate to the vault page
            page.goto("https://app.hyperliquid.xyz/vaults/0xdfc24b077bc1425ad1dea75bcb6f8158e10df303")
            print("Navigating to vault page...")
            
            # Wait for table to load with timeout
            page.wait_for_selector("table.vaults-table", timeout=30000)
            print("Table loaded successfully")
            
            # Extract all rows from the table
            rows = page.query_selector_all("table.vaults-table tr")
            print(f"Found {len(rows)} table rows")
            
            alerts = []
            
            for row in rows:
                # Skip header row
                if row.get("text_content")() == "Vaults":
                    continue
                
                # Check if this is a perpetual position row
                perp_cell = row.query_selector("td:has-text('Perp')")
                if not perp_cell:
                    continue
                
                # Extract data fields
                coin = row.query_selector("td:nth-child(2)")?.text_content()
                leverage = row.query_selector("td:nth-child(3)")?.text_content()
                size = row.query_selector("td:nth-child(4)")?.text_content()
                mark_price = row.query_selector("td:nth-child(5)")?.text_content()
                
                # Check if all required fields are present
                if not (coin and leverage and size and mark_price):
                    continue
                
                try:
                    # Convert size and mark price to numbers
                    size_num = float(size.replace(",", ""))
                    mark_price_num = float(mark_price.replace(",", ""))
                    
                    # Calculate position value
                    position_value = size_num * mark_price_num
                    
                    # Check threshold
                    if position_value > 50000:
                        alerts.append({
                            "coin": coin,
                            "size": size_num,
                            "mark_price": mark_price_num,
                            "position_value": position_value
                        })
                except ValueError as e:
                    print(f"Error parsing data: {e}")
            
            # Send email alerts
            if alerts:
                subject = "Perpetual Position Alert"
                body = "The following positions exceed \$50,000 USD:\n\n"
                for alert in alerts:
                    body += f"Coin: {alert['coin']}\n"
                    body += f"Size: {alert['size']}\n"
                    body += f"Mark Price: {alert['mark_price']}\n"
                    body += f"Position Value: ${alert['position_value']:.2f}\n\n"
                send_email(subject, body)
            else:
                subject = "No Perpetual Positions Exceeded Threshold"
                body = "No perpetual positions were found with a value exceeding \$50,000 USD."
                send_email(subject, body)
                
    except Exception as e:
        print(f"Script error: {e}")
    finally:
        if 'browser' in locals():
            browser.close()

if __name__ == "__main__":
    main()
