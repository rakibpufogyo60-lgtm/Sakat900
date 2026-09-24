import os
import sys
import asyncio
import subprocess
import requests

# ১. ব্যাকগ্রাউন্ডে অটোমেটিক Chromium ব্রাউজার ডাউনলোড করার ফাংশন
def auto_install_playwright_browsers():
    try:
        print("Playwright ব্রাউজার ডাউনলোড চেক করা হচ্ছে...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("Chromium ব্রাউজার সফলভাবে প্রস্তুত হয়েছে!")
    except Exception as e:
        print(f"ব্রাউজার ডাউনলোড করতে সমস্যা হয়েছে: {e}")

# বোট শুরুর আগেই ব্রাউজার ডাউনলোড নিশ্চিত করা
auto_install_playwright_browsers()

from playwright.async_api import async_playwright

# ==================== কনফিগারেশন ====================
TELEGRAM_BOT_TOKEN = "8222223746:AAGSX4HrPdDlvRBr7Gu2cjQ3sng72EioqE4"
TELEGRAM_CHAT_ID = "-1003885154692"

TRADINGVIEW_SESSION_ID = "dbd6bv5at1vl2byijtktvqfa09wxxatr"
TRADINGVIEW_SESSION_ID_SIGN = "v3:2PNozCRH1ZjhsSVqpjTrW7cPJjU89MXIgOV6/Gh2CwA="

GOLD_CHART_URL = "https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD&interval=1"
# ====================================================

def send_telegram_alert(message, image_path=None):
    try:
        if image_path:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as photo:
                payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message}
                files = {'photo': photo}
                requests.post(url, data=payload, files=files)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
            requests.post(url, data=payload)
    except Exception as e:
        print(f"টেলিগ্রাম এ এরর: {e}")

async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})

        await context.add_cookies([
            {
                'name': 'sessionid',
                'value': TRADINGVIEW_SESSION_ID,
                'domain': '.tradingview.com',
                'path': '/'
            },
            {
                'name': 'sessionid_sign',
                'value': TRADINGVIEW_SESSION_ID_SIGN,
                'domain': '.tradingview.com',
                'path': '/'
            }
        ])

        page = await context.new_page()
        print("Gold (XAUUSD) চার্ট লোড হচ্ছে...")
        await page.goto(GOLD_CHART_URL)
        await page.wait_for_load_state("networkidle")

        # ইন্ডিকেটর সেকশন
        indicator_button = page.locator("button[data-name='indicators']")
        if await indicator_button.is_visible():
            await indicator_button.click()
            await page.wait_for_timeout(2000)

        try:
            sakat_indicator = page.get_by_text("SAKAT", exact=True)
            if await sakat_indicator.is_visible():
                await sakat_indicator.click()
                print("SAKAT ইন্ডিকেটর যুক্ত হয়েছে!")
                
            close_button = page.locator("button[data-name='close']")
            if await close_button.is_visible():
                await close_button.click()
        except Exception as e:
            print(f"ইন্ডিকেটর লোড সমস্যা: {e}")

        await page.wait_for_timeout(5000)

        initial_buy_count = await page.locator("text='Buy'").count()
        initial_sell_count = await page.locator("text='Sell'").count()
        
        last_buy_count = initial_buy_count
        last_sell_count = initial_sell_count

        send_telegram_alert("🤖 Gold (XAUUSD) বোট সফলভাবে সার্ভারে চালু হয়েছে!")

        minute_counter = 0
        while True:
            screenshot_path = "gold_chart_live.png"
            await page.screenshot(path=screenshot_path)

            current_buy_count = await page.locator("text='Buy'").count()
            current_sell_count = await page.locator("text='Sell'").count()

            signal_detected = False
            signal_msg = ""

            if current_buy_count > last_buy_count:
                signal_detected = True
                signal_msg = "🚨 **নতুন BUY সিগন্যাল (Gold/XAUUSD)!** 🟢"
                last_buy_count = current_buy_count

            elif current_sell_count > last_sell_count:
                signal_detected = True
                signal_msg = "🚨 **নতুন SELL সিগন্যাল (Gold/XAUUSD)!** 🔴"
                last_sell_count = current_sell_count

            if signal_detected:
                send_telegram_alert(signal_msg, screenshot_path)
            else:
                minute_counter += 1
                caption_text = f"📊 Gold (XAUUSD) Live Chart Update #{minute_counter}"
                send_telegram_alert(caption_text, screenshot_path)

            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_bot())
