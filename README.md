
# Price Tracker Bot

A Telegram bot that helps users track prices of products on various websites. Users can add product URLs with a target price, and the bot will notify them when the product price drops below or matches the target price.

## Features

- **Add Products:** Track a product by providing its URL and your target price.
- **List Products:** View the products you are tracking along with their current and target prices.
- **Remove Products:** Stop tracking a product.
- **Price Alerts:** Get notified when a product's price meets or drops below your target.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A Telegram bot token (create one via [BotFather](https://core.telegram.org/bots#botfather))
- SQLite database (automatically created)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/umutkayash/price-tracker.git
   cd price-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your bot token:
   - Replace `TOKEN HERE` in `main.py` with your actual bot token.

4. Initialize the database:
   The database will be automatically created when you run the bot.

### Usage

Run the bot:
```bash
python main.py
```

### Bot Commands

- `/start` - Start the bot and view available commands.
- `/add <URL> <Target Price>` - Add a new product to track.
- `/list` - List all tracked products.
- `/remove` - Remove a product from tracking.

### Example

- To track a product:
  ```
  /add https://example.com/product 100.00
  ```
- To view tracked products:
  ```
  /list
  ```

## Technical Details

- **Dependencies:** 
  - [Aiogram](https://docs.aiogram.dev/)
  - [Aiohttp](https://docs.aiohttp.org/en/stable/)
  - [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- **Database:** SQLite for storing user-tracked products.
- **Concurrency:** Asynchronous programming with `asyncio` for handling updates and price checks.

## Future Enhancements

- Support for additional e-commerce sites.
- Advanced price filtering and history tracking.
- Multi-language support.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---
