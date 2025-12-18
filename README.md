Telegram bot for automated monitoring and notifications, built with **Python**.  
The project focuses on background processing, filtering logic, and scheduled tasks.

## Features
- Telegram bot for notifications
- Subscription-based logic
- Background jobs and scheduler
- Data collection from external sources
- Filtering and matching rules
- Role-based access
- Modular architecture

## Tech Stack
- Python 3.10+
- Telegram Bot API
- Async execution model
- Scheduler (background jobs)
- External data sources integration

## Project Structure
.
├── handlers/ # Telegram handlers
├── services/ # Business logic
├── scheduler/ # Background jobs
├── data_sources/ # External data collectors
├── filter_engine/ # Filtering logic
├── notifier/ # Notifications
├── config/ # Configuration
├── main.py # Entry point

bash
Копировать код

## Setup & Run
```bash
git clone https://github.com/naimaaan/zakupbot.git
cd zakupbot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
python main.py
Notes
Project was developed as a real automation bot

Focus on stability and extensibility
