import logging
import sqlite3
import aiohttp
import asyncio
from aiogram import Bot
from bs4 import BeautifulSoup
import re
from typing import Tuple, List, Optional

BOT_TOKEN = 'TOKEN HERE'
db_path = "products.db"
SIGNATURE = """
╔══════════════════════╗
║    by                ║
║    UMUTKAYASH        ║
╚══════════════════════╝
"""

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            target_price REAL,
            user_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

async def extract_prices_from_html(html: str) -> List[Tuple[float, str]]:
    soup = BeautifulSoup(html, "html.parser")
    price_data = []
    
    price_patterns = [
        r"price",
        r"amount",
        r"cost",
        r"value",
        r"currency",
        r"sale",
        r"discount",
        r"regular"
    ]
    
    for pattern in price_patterns:
        for element in soup.find_all(class_=re.compile(pattern, re.I)):
            text = element.get_text(strip=True)
            if text:
                price_match = re.search(r'[\d.,]+', text)
                if price_match:
                    try:
                        price_str = price_match.group().replace(',', '.')
                        if price_str.count('.') > 1:
                            price_str = price_str.replace('.', '', price_str.count('.') - 1)
                        price = float(price_str)
                        context = element.parent.get_text(strip=True)[:100] if element.parent else text
                        price_data.append((price, context))
                    except ValueError:
                        continue
    
    return price_data

async def fetch_price_and_details(url: str, target_price: float) -> Tuple[Optional[float], Optional[str], Optional[str], List[Tuple[float, str]]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10)) as session:
            async with session.get(url, headers=headers, max_redirects=5) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    price_data = await extract_prices_from_html(html)
                    
                    if not price_data:
                        return None, None, None, []
                    
                    price_data.sort(key=lambda x: abs(x[0] - target_price))
                    closest_price = price_data[0][0]
                    product_name = soup.title.string.strip() if soup.title else "Product"
                    
                    description = None
                    desc_tag = soup.find("meta", attrs={"name": "description"})
                    if desc_tag and desc_tag.get("content"):
                        description = desc_tag["content"].strip()
                    
                    return closest_price, product_name, description, price_data
                else:
                    logging.error(f"Unexpected response status: {response.status}")
                    return None, None, None, []
    except Exception as e:
        logging.error(f"Error fetching price and details: {e}")
        return None, None, None, []

async def check_products():
    while True:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, target_price, user_id FROM products")
        products = cursor.fetchall()
        conn.close()

        for product_id, url, target_price, user_id in products:
            fetched_price, name, description, _ = await fetch_price_and_details(url, target_price)
            if fetched_price is not None and fetched_price <= target_price:
                await bot.send_message(
                    user_id,
                    f"🎉 Price Drop Alert!\n\n"
                    f"Product: {name}\n"
                    f"URL: {url}\n"
                    f"Target Price: ${target_price:.2f}\n"
                    f"Current Price: ${fetched_price:.2f}\n"
                    f"Description: {description if description else 'Not found'}\n\n"
                    f"{SIGNATURE}"
                )
        
        await asyncio.sleep(30)

async def handle_updates():
    offset = 0
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    message = update.message
                    if message.text.startswith('/start'):
                        await bot.send_message(
                            message.chat.id,
                            f"Welcome to Price Tracker Bot!\n\n"
                            f"Commands:\n"
                            f"/add <URL> <Target Price> - Add new product\n"
                            f"/list - List all products\n"
                            f"/remove - Remove product\n\n"
                            f"{SIGNATURE}"
                        )
                    elif message.text.startswith('/add'):
                        args = message.text.split()[1:]
                        if len(args) < 2:
                            await bot.send_message(message.chat.id, "❌ Invalid format. Usage: /add <URL> <Target Price>")
                            continue
                        
                        url, target_price = args[0], args[1]
                        try:
                            target_price = float(target_price)
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO products (url, target_price, user_id) VALUES (?, ?, ?)",
                                (url, target_price, message.chat.id)
                            )
                            conn.commit()
                            conn.close()
                            await bot.send_message(
                                message.chat.id, 
                                f"✅ Product added successfully!\n\n{SIGNATURE}"
                            )
                        except ValueError:
                            await bot.send_message(message.chat.id, "❌ Please enter a valid price!")
                    
                    elif message.text.startswith('/list'):
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, url, target_price FROM products WHERE user_id = ?", (message.chat.id,))
                        products = cursor.fetchall()
                        conn.close()
                        
                        if not products:
                            await bot.send_message(
                                message.chat.id, 
                                f"📝 No products being tracked.\n\n{SIGNATURE}"
                            )
                        else:
                            for idx, (product_id, url, target_price) in enumerate(products, 1):
                                fetched_price, name, description, all_prices = await fetch_price_and_details(url, target_price)
                                
                                if fetched_price:
                                    message_text = (
                                        f"🔍 Product {idx}:\n"
                                        f"📌 {name}\n"
                                        f"🔗 {url}\n"
                                        f"🎯 Target: ${target_price:.2f}\n"
                                        f"💰 Current: ${fetched_price:.2f}\n\n"
                                        f"📊 All Detected Prices:\n"
                                    )
                                    
                                    for price, context in all_prices[:5]:
                                        message_text += f"- ${price:.2f} ({context})\n"
                                    
                                    message_text += f"\n{SIGNATURE}"
                                    
                                    await bot.send_message(message.chat.id, message_text)
                                else:
                                    await bot.send_message(
                                        message.chat.id,
                                        f"❌ Product {idx}:\n"
                                        f"🔗 {url}\n"
                                        f"Unable to fetch price information.\n\n"
                                        f"{SIGNATURE}"
                                    )
                    
                    elif message.text.startswith('/remove'):
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM products WHERE user_id = ?", (message.chat.id,))
                        if not cursor.fetchall():
                            await bot.send_message(
                                message.chat.id, 
                                f"❌ No products to remove.\n\n{SIGNATURE}"
                            )
                            conn.close()
                            continue
                        
                        cursor.execute("SELECT id, url, target_price FROM products WHERE user_id = ?", (message.chat.id,))
                        products = cursor.fetchall()
                        
                        msg = f"🗑 Enter the number of the product to remove:\n\n"
                        for idx, (product_id, url, target_price) in enumerate(products, 1):
                            msg += f"{idx}. {url} - ${target_price:.2f}\n"
                        msg += f"\n{SIGNATURE}"
                        
                        await bot.send_message(message.chat.id, msg)
                        
                        try:
                            response = await bot.get_updates(offset=offset, timeout=60)
                            if response and response[-1].message and response[-1].message.text:
                                try:
                                    idx = int(response[-1].message.text)
                                    if 1 <= idx <= len(products):
                                        product_id = products[idx-1][0]
                                        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                                        conn.commit()
                                        await bot.send_message(
                                            message.chat.id, 
                                            f"✅ Product {idx} removed successfully.\n\n{SIGNATURE}"
                                        )
                                    else:
                                        await bot.send_message(message.chat.id, "❌ Invalid product number.")
                                except ValueError:
                                    await bot.send_message(message.chat.id, "❌ Invalid input.")
                        except asyncio.TimeoutError:
                            await bot.send_message(message.chat.id, "⏰ Timeout. Please try again.")
                        
                        conn.close()
                
                offset = update.update_id + 1
        
        except Exception as e:
            logging.error(f"Error in handle_updates: {e}")
            await asyncio.sleep(5)

async def main():
    init_db()
    await asyncio.gather(handle_updates(), check_products())

if __name__ == "__main__":
    asyncio.run(main())