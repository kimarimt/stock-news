import requests
import os
import math
import html
from datetime import datetime, timedelta
from dotenv import load_dotenv
from dataclasses import dataclass

STOCK = 'AAPL'
COMPANY_NAME = 'Apple Inc'
ALPHA_VANTAGE_URL = 'https://www.alphavantage.co/query'
NEWS_URL = 'https://newsapi.org/v2/everything'
load_dotenv()


@dataclass
class Article:
    headline: str
    brief: str


def get_difference_percentage():
    api_key = os.getenv('ALPHA_VANTAGE_KEY')
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': STOCK,
        'apikey': api_key
    }
    response = requests.get(
        url=ALPHA_VANTAGE_URL,
        params=params
    )
    response.raise_for_status()

    daily = response.json()['Time Series (Daily)']
    dates = list(daily.keys())
    yesterday = float(daily[dates[1]]['4. close'])
    prior_to_yesterday = float(daily[dates[2]]['4. close'])
    difference = yesterday - prior_to_yesterday
    abs_difference = abs(difference)
    average = (yesterday + prior_to_yesterday) / 2
    percentage = math.ceil((abs_difference / average) * 100)

    return difference, percentage


def get_articles():
    api_key = os.getenv('NEWS_KEY')
    params = {
        'q': COMPANY_NAME,
        'from': (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'apiKey': api_key,
        'sortBy': 'popularity'
    }

    response = requests.get(
        url=NEWS_URL,
        params=params,
    )
    response.raise_for_status()

    articles = []
    data = response.json()['articles'][:3]
    for entry in data:
        article = Article(
            headline=entry['title'].split(' - ')[0],
            brief=html.unescape(entry['description'])
        )
        articles.append(article)

    return articles


def send_message(message):
    bot_token = os.getenv('STOCK_NEWS_BOT')
    chat_id = os.getenv('CHAT_ID')
    url = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' \
          + chat_id + '&parse_mode=Markdown&text=' + message
    response = requests.get(url)
    response.raise_for_status()


def main():
    difference, percentage = get_difference_percentage()

    if percentage >= 5:
        starter = '+' if difference > 0 else '-'
        for article in get_articles():
            message = f'''
{STOCK}: {starter}{percentage}%
{article.headline}
{article.brief}
    '''
            send_message(message)
    else:
        message = f'No significant changes to {STOCK} stock'
        send_message(message)


if __name__ == '__main__':
    main()
