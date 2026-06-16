# Payment Quick Start

1. Copy the example env file and fill in your sandbox credentials:

```bash
cp .env.example .env
# Edit .env and set CONSUMER_KEY, CONSUMER_SECRET, PASSKEY, CALLBACK_URL
```

2. Initialize the local database (tables are created automatically on startup):

```bash
python App.py
# or run with uvicorn
uvicorn App:app --reload --host 0.0.0.0 --port 8000
```

3. Call the STK push endpoint from the frontend or via curl:

```bash
curl -X POST http://localhost:8000/payments/stk-push \
  -H 'Content-Type: application/json' \
  -d '{"phone_number":"254712345678","amount":1000}'
```

4. Monitor logs for callback processing and DB updates.
