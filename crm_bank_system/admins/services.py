import requests
from datetime import datetime


def set_default_currencies_list():
    return ['bitcoin', 'ethereum', 'tether', 'solana', 'ripple']

def fetch_crypto_data(crypto_id):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    params = {
        "vs_currency": "usd",  # Валюта - USD
        "days": 3  # Последние 7 дней
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data for {crypto_id} from CoinGecko API")

def process_data_for_single_currency(crypto):
    data = fetch_crypto_data(crypto)
    prices = data.get("prices", [])

    dates = []
    prices_list = []

    for price_entry in prices:
        timestamp, price = price_entry
        date = datetime.utcfromtimestamp(timestamp // 1000).strftime('%Y-%m-%d')
        dates.append(date)
        prices_list.append(price)

    chart_data = [["Day", crypto]]
    for i in range(len(dates)):
        chart_data.append([dates[i], prices_list[i]])

    return chart_data