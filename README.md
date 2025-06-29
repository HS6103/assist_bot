# assist_bot

Assist Bot is a modular chatbot and meeting assistant platform built with Python. It supports intent recognition, meeting record management, and integration with external APIs such as Articut and Loki for natural language processing.

## Features

- **Meeting Record Management**: Create, manage, and backup meeting records.
- **Intent Recognition**: Uses Loki API for intent detection and argument extraction.
- **Extensible Architecture**: Modular design for easy extension and maintenance.
- **Backup Utilities**: Automated backup for intents and meeting records.

## Project Structure

```
assist_bot/
├── assist_backend/         # Django backend (database, API, notifications)
├── assist_datetime/        # Date/time assistant module
├── assist_record/          # Meeting record assistant module (WIP)
├── Loki_Backup/            # Backup directory for Loki intent files
├── Discord_bot_assist.py   # Discord bot integration
├── README.md
├── requirements.txt
├── test.py
└── account.info            # Account credentials for APIs
```

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/assist_bot.git
   cd assist_bot
   ```

2. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   - Edit `account.info` with your Articut and Loki API credentials.

## Usage

### Discord Bot

To start the Discord bot:

```sh
python Discord_bot_assist.py
```

### Backend

To run the Django backend:

```sh
cd assist_backend
python manage.py runserver
```

## Customization

- **Intents**: Add or modify intents in `assist_record/intent`.
- **Prompts & Replies**: Edit chatbot prompts and reply templates in the respective module directories.
- **User Dictionary**: Update user-defined dictionaries for custom NLP needs.

## Backup

Backups of intents and meeting records are stored in the `Loki_Backup` directory.

Backups of meeting notifications are stored in the `backup.json` file.

## Requirements

- Python 3.11+
- [ArticutAPI](https://github.com/Droidtown/ArticutAPI)
- requests

See `requirements.txt` files for details.

## License

MIT License

---

## Author

蕭煦宸 Hsiao Hsu-chen (Simon)
