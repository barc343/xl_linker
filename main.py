import os
from dotenv import load_dotenv, find_dotenv
import json
from datetime import datetime
import logging
from config import ROOT_PATH

logging.basicConfig(filename=ROOT_PATH+'/logs/debug.log', encoding='utf-8', level=logging.INFO)

from api.baselinker import BaselinkerApi
from api.fakturaxl import FakturaXLApi

load_dotenv(find_dotenv())

BL_API_KEY = os.environ.get("BL_API_KEY")
FXL_API_KEY = os.environ.get("FXL_API_KEY")

# curl 'https://api.baselinker.com/connector.php' -H 'X-BLToken: 1-23-ABC' --data-raw 'method=getOrders&parameters=%7B%22date_from%22%3A+1407341754%7D'


if __name__ == '__main__':
    bl_api = BaselinkerApi(BL_API_KEY)
    fxl_api = FakturaXLApi(FXL_API_KEY)
    bl_invoices = bl_api.get_last_invoices()
    for bl_invoice in bl_invoices['invoices']:
        print(bl_invoice)
        invoice_xml = fxl_api.create_xml(bl_invoice)
        if fxl_api.check_invoice_exist(bl_invoice['invoice_id']):
            logging.info('{} Faktura {} istnieje już w bazie connectora - pomijam'.format(datetime.now(), bl_invoice['invoice_id']))
            continue
        else:
            invoice_to_send = fxl_api.create_invoice(invoice_xml, bl_invoice['invoice_id'])
            status = bl_api.ovveride_invoice_file(invoice_to_send)
            if status == 'SUCCESS':
                fxl_api.update_invoice_send_status(bl_invoice['invoice_id'])
                logging.info('{} Faktura {} została dodana do systemu FakturaXL oraz przesłana do systemu BaseLinker'.format(datetime.now(), bl_invoice['invoice_id']))
            else:
                logging.warning(
                    '{} Faktura {} nie została przesłana do BaseLinker'.format(
                        datetime.now(), bl_invoice['invoice_id']))
    print('Synchronizacja została zakończona - więcej informacji znajdziesz w logs/debug.log')

