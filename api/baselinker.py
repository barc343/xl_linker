import json
import requests
from datetime import datetime, timedelta

# curl 'https://api.baselinker.com/connector.php' -H 'X-BLToken: 1-23-ABC' --data-raw 'method=getOrders&parameters=%7B%22date_from%22%3A+1407341754%7D'
class BaselinkerApi():
    def __init__(self, api_key):
        self.host = 'https://api.baselinker.com/connector.php'
        self.api_key = api_key

    def create_request_body(self, method, json_data):
        req_data = {
            "method": method,
            "parameters": json_data
        }
        return req_data

    def create_headers(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-BLToken": self.api_key
        }
        return headers

    def get_last_invoices(self):
        d = datetime.today() - timedelta(days=7)
        params = {
            "date_from": int(d.timestamp())
        }
        res = self.post('getInvoices', json.dumps(params))
        return res

    def ovveride_invoice_file(self, inv_data):
        res = self.post('addOrderInvoiceFile', json.dumps(inv_data))
        if res:
            return res['status']


    def post(self, method, json_data):
        body = self.create_request_body(method, json_data)
        headers = self.create_headers()
        res = requests.post(self.host, data=body, headers=headers)
        return res.json()
