import requests
from datetime import datetime

from core.models import TCoreCurrency
from crm.models import CrmCurrencyConversionHistory

"""
Real Time Currency conversion using Alpha Vantage.
Link: https://www.alphavantage.co/support/#api-key
Doc: https://www.alphavantage.co/documentation/
API_KEY = 'ZA3SH9OKTHX2IP43'
"""


def realtime_exchange_rate(from_currency='USD', to_currency='INR'):
    current_date = datetime.now()
    from_currency_obj = TCoreCurrency.objects.filter(code=from_currency, is_deleted=False).first()
    to_currency_obj = TCoreCurrency.objects.filter(code=to_currency, is_deleted=False).first()
    currency_obj = CrmCurrencyConversionHistory.cmobjects.filter(from_currency=from_currency_obj,
                                            to_currency=to_currency_obj, created_at__date=current_date.date()).last()
    rate = 1.0
    if currency_obj:
        rate = currency_obj.rate
    else:
        URL = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey=ZA3SH9OKTHX2IP43'
        url = URL.format(from_currency, to_currency)
        response = requests.get(url)
        data = response.json()
        rate = data['Realtime Currency Exchange Rate']['5. Exchange Rate']
        CrmCurrencyConversionHistory.objects.create(from_currency=from_currency_obj, to_currency=to_currency_obj, rate=rate)
    return rate


def realtime_exchange_value(from_currency='USD', to_currency='INR', value=0.0):
    rate = realtime_exchange_rate(from_currency=from_currency, to_currency=to_currency)
    total_value = float(rate)*float(value)
    return round(total_value, 2) if total_value else 0.0

