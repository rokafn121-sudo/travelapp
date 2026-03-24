import yfinance as yf
from datetime import datetime

tickers = {
    "USD": "KRW=X",
    "EUR": "EURKRW=X",
    "JPY": "JPYKRW=X"
}

print("Testing tickers...")
for currency, ticker in tickers.items():
    try:
        data = yf.download(ticker, period="1d")
        if not data.empty:
            print(f"{currency} ({ticker}): Success. Rate ~ {data['Close'].iloc[-1].item()}")
        else:
            print(f"{currency} ({ticker}): No data found.")
    except Exception as e:
        print(f"{currency} ({ticker}): Error - {e}")
