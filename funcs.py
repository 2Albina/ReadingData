import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime


def get_base_date():
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()
    cursor.execute('SELECT base_date FROM parameters ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def save_base_date(base_date):
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO parameters (base_date) VALUES (?)', (base_date,))
    conn.commit()
    conn.close()


def sync_currency_data(date, currency, rate):
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO currency_rates (date, currency, rate)
    VALUES (?, ?, ?)
    ON CONFLICT(date, currency) DO UPDATE SET rate=excluded.rate
    ''', (date, currency, rate))
    conn.commit()
    conn.close()


def calculate_relative_changes(base_date):
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()

    cursor.execute('SELECT currency, rate FROM currency_rates WHERE date = ?', (base_date,))
    base_rates = cursor.fetchall()

    for base_currency, base_rate in base_rates:
        cursor.execute('SELECT date, rate FROM currency_rates WHERE currency = ?', (base_currency,))
        current_rates = cursor.fetchall()

        for current_date, current_rate in current_rates:
            relative_change = ((current_rate - base_rate) / base_rate) * 100
            cursor.execute('''
            INSERT INTO relative_changes (cur_date, currency, relative_change)
            VALUES (?, ?, ?)
            ON CONFLICT(cur_date, currency) DO UPDATE SET relative_change=excluded.relative_change
            ''', (current_date, base_currency, relative_change))

    conn.commit()
    conn.close()


def get_relative_changes():
    conn = sqlite3.connect('ReadingData.db')
    cursor = conn.cursor()
    cursor.execute('SELECT cur_date, currency, relative_change FROM relative_changes ORDER BY currency, cur_date')
    relative_changes = cursor.fetchall()
    conn.close()
    return relative_changes


def fetch_exchange_rates(start_date, end_date, currency_code):
    url = f"https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur={currency_code}"
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    url += f"&bd={start_date_obj.day}&bm={start_date_obj.month}&by={start_date_obj.year}"
    url += f"&ed={end_date_obj.day}&em={end_date_obj.month}&ey={end_date_obj.year}"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_='karramba')
    rows = table.find_all('tr')

    dates = []
    rates = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 1:
            date_str = cols[0].text.strip()
            rate_str = cols[2].text.strip().replace(',', '.')
            date = datetime.strptime(date_str, '%d.%m.%Y')
            rate = float(rate_str)
            dates.append(date)
            rates.append(rate)

    return pd.DataFrame({'Date': dates, 'Rate': rates})

