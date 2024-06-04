from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from funcs import get_base_date, save_base_date, sync_currency_data, calculate_relative_changes, get_relative_changes, fetch_exchange_rates

currency = {52148: 'USD', 52170: 'EUR', 52146: 'GBP', 52246: 'JPY', 52158: 'TRY', 52238: 'INR', 52207: 'CNY'}

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/reading')
def reading():
    return render_template('reading.html')


@app.route('/changes')
def changes():
    return render_template('changes.html')


@app.route('/get-changes', methods=['POST'])
def get_changes():
    countries = request.form.getlist('countries')
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    global currency
    df_list = []
    for country in countries:
        df = fetch_exchange_rates(start_date, end_date, int(country))
        df.set_index('Date', inplace=True)
        df = df.pct_change().fillna(0)
        df.columns = [currency[int(country)]]
        df_list.append(df)

    if df_list:
        combined_df = pd.concat(df_list, axis=1)
        print('combined_df ', combined_df)
        fig = px.line(combined_df, x=combined_df.index, y=combined_df.columns,
                      labels={'value': 'Relative Change', 'index': 'Date'})
        graph = fig.to_html(full_html=False)

        return render_template('changes.html', graph=graph, countries=countries, start_date=start_date, end_date=end_date)


@app.route('/get-rates', methods=['POST'])
def get_rates():
    # курсы валют
    start_date = request.form['start-date']
    end_date = request.form['end-date']

    start_date_parts = start_date.split('-')
    end_date_parts = end_date.split('-')

    bd = start_date_parts[2]
    bm = start_date_parts[1]
    by = start_date_parts[0]

    ed = end_date_parts[2]
    em = end_date_parts[1]
    ey = end_date_parts[0]

    courses_arr = []
    global currency
    for cur in (currency.keys()):
        url = f"https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur={cur}&bd={bd}&bm={bm}&by={by}&ed={ed}&em={em}&ey={ey}"

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        courses = soup.find('table', class_='karramba')

        description = ''
        caption = courses.find('caption')
        if caption:
            description = caption.text

        courses_headers = [th.text for th in courses.find_all('th')]

        courses_data = []
        for row in courses.find_all('tr'):
            columns = row.find_all('td')
            if columns:
                courses_data.append([col.text for col in columns])
        results = {
            'description': description,
            'courses_headers': courses_headers,
            'courses_data': courses_data
        }
        courses_arr.append(results)

        base_date = get_base_date() or courses_data[0][0]
        for row in courses_data:
            if len(row) >= 3:
                date = row[0]
                rate = float(row[2].replace(',', '.'))
                sync_currency_data(date, currency[cur], rate)

        if not get_base_date():
            save_base_date(base_date)

        calculate_relative_changes(base_date)

    # Таблица относительных изменений курса
    relative_changes_data = get_relative_changes()

    # список валют стран мира
    world_currencies_url = "https://www.iban.ru/currency-codes"
    response = requests.get(world_currencies_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    currencies_table = soup.find('table', class_='table table-bordered downloads tablesorter')
    world_currencies_data = []
    world_currencies_headers = []

    if currencies_table:
        world_currencies_headers = [th.text for th in currencies_table.find_all('th')]
        for row in currencies_table.find_all('tr'):
            columns = row.find_all('td')
            if columns:
                world_currencies_data.append([col.text for col in columns])

    results = {
        "courses_arr": courses_arr,
        "base_date": base_date,
        "relative_changes_data": relative_changes_data,
        "world_currencies_table_headers": world_currencies_headers,
        "world_currencies_table_data": world_currencies_data
    }

    return render_template('reading.html', results=results)


if __name__ == '__main__':
    app.run(debug=True)
