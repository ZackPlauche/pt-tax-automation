from __future__ import annotations

import os
from datetime import datetime, date
from decimal import Decimal

import requests
from currency_converter import CurrencyConverter, ECB_URL
from dotenv import load_dotenv
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.keys import Keys as KEYS
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Collect details of the invoice

class Invoice(BaseModel):
    amount: Decimal
    currency: str = 'USD'
    date: date
    client_name: str
    description: str

    @classmethod
    def from_input(cls):
        client_name = input('Enter the full name of the client: ')
        amount = input('Enter the invoice amount in USD: $')
        date = input('Enter the date (format: YYYY-MM-DD): ')
        description = input('Enter the description: ')
        return cls(amount=amount, date=date, client_name=client_name, description=description)

    def to_currency(self, to_currency: str) -> Invoice:
        return Invoice(
            **self.model_dump(exclude=['amount', 'currency']),
            currency=to_currency,
            amount=convert_currency(self.amount, self.currency, to_currency, self.date),
        )


# Convert USD to Euro value of that day
# 1. Get the latest exchange rates
def convert_currency(amount: int | float | Decimal, from_currency: str, to_currency: str, date: date) -> Decimal:

    # 1. Get the latest exchange rates
    filename = f'ecb_{datetime.today().date():%Y%m%d}.zip'
    if not os.path.isfile(filename):
        response = requests.get(ECB_URL)
        with open(filename, 'wb') as f:
            f.write(response.content)

    # 2. Convert the amount to EUR
    amount = CurrencyConverter(filename).convert(amount, from_currency, to_currency, date)
    return amount


# Submit the invoice to the client
class TaxPortalWebsite:
    PAGES = {
        'login': 'https://www.acesso.gov.pt/v2/loginForm?partID=SIRE&path=/recibos/portal/',
        'login success': 'https://irs.portaldasfinancas.gov.pt/recibos/;sireinter_JSessionID=',
        'invoice start': 'https://irs.portaldasfinancas.gov.pt/recibos/portal/emitir/emitirDocumentos',
        'invoice form': 'https://irs.portaldasfinancas.gov.pt/recibos/portal/emitir/emitirfatura'
    }

    def __init__(self, login: bool = True, headless: bool = False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        self.browser = webdriver.Chrome()
        if login:
            self.login()

    def login(self):
        self.browser.get(self.PAGES['login'])
        load_dotenv()
        nif = os.getenv('NIF')
        tax_portal_password = os.getenv('TAX_PORTAL_PASSWORD')
        tab_labels = self.browser.find_elements('css selector', '.tab-label')
        tab_labels[1].click()
        self.browser.find_element('id', 'username').send_keys(nif)
        self.browser.find_element('id', 'password-nif').send_keys(tax_portal_password)
        self.browser.find_element('id', 'sbmtLogin').click()
        WebDriverWait(self.browser, 10).until(EC.url_contains(self.PAGES['login success']))

    def submit_invoice(self, invoice: Invoice, submit: bool = True):
        if not invoice.currency == 'EUR':
            invoice = invoice.to_currency('EUR')
        invoice_form_url = f'{self.PAGES["invoice form"]}?dataCopia={invoice.date:%Y-%m-%d}&tipoRecibo=FR'
        self.browser.get(invoice_form_url)
        self.browser.find_element('css selector', 'select[name="pais"]').send_keys('EST', KEYS.ENTER)
        self.browser.find_element('css selector', 'input[name="nomeAdquirente"]').send_keys(invoice.client_name)
        self.browser.find_element('css selector', 'input[name="titulo"][value="1"]').click()
        self.browser.find_element('css selector', 'textarea[name="servicoPrestado"]').send_keys(invoice.description)
        self.browser.find_element('css selector', 'input[name="valorBase"]').send_keys(f'{invoice.amount:.2f}')
        issue_button = [button for button in self.browser.find_elements('css selector', 'button') if button.text == 'EMITIR'][0]
        os.system('pause')
        if submit:
            issue_button.click()
        

        

