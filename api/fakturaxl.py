import json
from xml.dom import minidom
import requests
import xmltodict
import base64
from datetime import datetime, timedelta
import xml.etree.ElementTree as et
from db.main import MainDB

from config import ROOT_PATH

def timestamp_to_date(timestamp):
    dt_obj = datetime.fromtimestamp(timestamp)
    date_time = dt_obj.strftime("%Y-%m-%d")
    return date_time


def count_payday(timestamp):
    dt_obj = datetime.fromtimestamp(timestamp)
    payday = dt_obj + timedelta(days=7)
    return datetime.timestamp(payday)


# curl 'https://api.baselinker.com/connector.php' -H 'X-BLToken: 1-23-ABC' --data-raw 'method=getOrders&parameters=%7B%22date_from%22%3A+1407341754%7D'
class FakturaXLApi():
    def __init__(self, api_key):
        self.host = 'https://program.fakturaxl.pl/api/'
        self.api_key = api_key
        self.db = MainDB()

    def create_request_body(self, method, json_data):
        req_data = {
            "method": method,
            "parameters": json_data
        }
        return req_data

    def create_headers(self):
        headers = {
            'Content-Type': 'application/xml',
        }
        return headers

    def create_xml(self, bl_invoice_data=None):
        root = et.Element("dokument")

        api_token = et.Element("api_token")
        api_token.text = self.api_key
        root.append(api_token)

        typ_faktury = et.Element("typ_faktury")
        typ_faktury.text = str(0)
        root.append(typ_faktury)

        obliczaj_sume_wartosci_faktury_wg = et.Element("obliczaj_sume_wartosci_faktury_wg")
        obliczaj_sume_wartosci_faktury_wg.text = str(0)
        root.append(obliczaj_sume_wartosci_faktury_wg)

        numer_faktury = et.Element("numer_faktury")
        root.append(numer_faktury)

        data_wystawienia = et.Element("data_wystawienia")
        data_wystawienia.text = timestamp_to_date(bl_invoice_data['date_add'])
        root.append(data_wystawienia)

        data_sprzedazy = et.Element("data_sprzedazy")
        data_sprzedazy.text = timestamp_to_date(bl_invoice_data['date_sell'])
        root.append(data_sprzedazy)

        termin_platnosci_data = et.Element("termin_platnosci_data")
        termin_platnosci_data.text = timestamp_to_date(count_payday(bl_invoice_data['date_add']))
        root.append(termin_platnosci_data)

        if 'total_price_brutto' in bl_invoice_data:
            data_oplacenia = et.Element("data_oplacenia")
            data_oplacenia.text = timestamp_to_date(bl_invoice_data['date_sell'])
            root.append(data_oplacenia)

            kwota_oplacona = et.Element("kwota_oplacona")
            kwota_oplacona.text = bl_invoice_data['total_price_brutto']
            root.append(kwota_oplacona)
        else:
            kwota_oplacona = et.Element("kwota_oplacona")
            kwota_oplacona.text = str(0)
            root.append(kwota_oplacona)

        uwagi = et.Element("uwagi")
        root.append(uwagi)

        waluta = et.Element("waluta")
        waluta.text = "PLN"
        root.append(waluta)

        rodzaj_platnosci = et.Element("rodzaj_platnosci")
        rodzaj_platnosci.text = "Przelew"
        root.append(rodzaj_platnosci)

        id_dzialy_firmy = et.Element("id_dzialy_firmy")
        id_dzialy_firmy.text = "88997"
        root.append(id_dzialy_firmy)

        imie_nazwisko_wystawcy = et.Element("imie_nazwisko_wystawcy")
        imie_nazwisko_wystawcy.text = "Janusz Cieślak"
        root.append(imie_nazwisko_wystawcy)

        wyslij_dokument_do_klienta_emailem = et.Element("wyslij_dokument_do_klienta_emailem")
        wyslij_dokument_do_klienta_emailem.text = str(1)
        root.append(wyslij_dokument_do_klienta_emailem)

        nabywca = et.Element("nabywca")
        root.append(nabywca)

        if bl_invoice_data and bl_invoice_data['invoice_fullname'] == '':
            firma_lub_osoba_prywatna = et.SubElement(nabywca, "firma_lub_osoba_prywatna")
            firma_lub_osoba_prywatna.text = str(0)

            nazwa = et.SubElement(nabywca, "nazwa")
            nazwa.text = bl_invoice_data['invoice_company']
        else:
            firma_lub_osoba_prywatna = et.SubElement(nabywca, "firma_lub_osoba_prywatna")
            firma_lub_osoba_prywatna.text = str(1)

            imie_nazwisko_odbiorcy = et.SubElement(nabywca, "imie_nazwisko_odbiorcy")
            imie_nazwisko_odbiorcy.text = bl_invoice_data['invoice_fullname']

        # imie = et.SubElement(nabywca, "imie")
        # imie.text = "imie"
        #
        # nazwisko = et.SubElement(nabywca, "nazwisko")
        # nazwisko.text = "nazwisko"

        nip = et.SubElement(nabywca, "nip")
        nip.text = bl_invoice_data['invoice_nip']

        ulica_i_numer = et.SubElement(nabywca, "ulica_i_numer")
        ulica_i_numer.text = bl_invoice_data['invoice_address']

        kod_pocztowy = et.SubElement(nabywca, "kod_pocztowy")
        kod_pocztowy.text = bl_invoice_data['invoice_postcode']

        miejscowosc = et.SubElement(nabywca, "miejscowosc")
        miejscowosc.text = bl_invoice_data['invoice_city']

        kraj = et.SubElement(nabywca, "kraj")
        kraj.text = bl_invoice_data['invoice_country_code']

        for item in bl_invoice_data['items']:
            faktura_pozycje = et.Element("faktura_pozycje")
            root.append(faktura_pozycje)

            nazwa = et.SubElement(faktura_pozycje, "nazwa")
            nazwa.text = item['name']

            ilosc = et.SubElement(faktura_pozycje, "ilosc")
            ilosc.text = str(item['quantity'])

            vat = et.SubElement(faktura_pozycje, "vat")
            vat.text = str(23)

            wartosc_brutto = et.SubElement(faktura_pozycje, "wartosc_brutto")
            wartosc_brutto.text = str(item['price_brutto']*item['quantity'])

        tree = et.ElementTree(root)

        xml_str = et.tostring(tree.getroot(), encoding='UTF-8')
        return xml_str

    def check_invoice_exist(self, bl_invoice_id):
        res = self.db.get_single_row('SELECT * FROM connected_invoices WHERE bl_inv_id = {}'.format(bl_invoice_id))
        if res:
            return res[0]
        else:
            return None

    def get_invoice_pdf_base64(self, fxl_inv_id):
        conn_str = 'https://program.fakturaxl.pl/' + "dokument_export.php" + '?api=' + self.api_key + '&dokument_id=' + fxl_inv_id + '&pdf=1'
        res = requests.get(conn_str)
        # open(res.headers.get("Content-Disposition").split("filename=")[1], "wb").write(res.content)
        file_url = ROOT_PATH+'/files/{}.pdf'.format(fxl_inv_id)
        open(file_url, "wb").write(res.content)
        with open(file_url, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        return encoded_string

    def create_invoice(self, xml_data, bl_invoice_id):
        res = self.post(xml_data)
        res_as_dict = xmltodict.parse(res)
        fxl_invoice_id = res_as_dict['dokument']['dokument_id']
        fxl_inv_number = res_as_dict['dokument']['dokument_nr']
        # Print the dictionary
        now = datetime.now().timestamp()
        insert_sql = '''
            INSERT INTO connected_invoices(bl_inv_id, fxl_inv_id, connect_date, file_changed_in_bl) VALUES ({}, {}, {}, {})
        '''.format(str(bl_invoice_id), str(fxl_invoice_id), str(now), 0)
        self.db.insert(insert_sql)
        res = {
            "external_invoice_number": fxl_inv_number,
            "invoice_id": bl_invoice_id,
            "file": 'data:' + self.get_invoice_pdf_base64(fxl_invoice_id).decode('utf-8')
        }
        return res


    def update_invoice_send_status(self, bl_invoice_id):
        sql = ''' UPDATE connected_invoices
                  SET file_changed_in_bl = 1
                  WHERE bl_inv_id = {}'''.format(bl_invoice_id)
        self.db.update(sql)


    def post(self, xml_data):
        headers = self.create_headers()
        res = requests.post(self.host + 'dokument_dodaj.php', data=xml_data, headers=headers)
        return res.text

