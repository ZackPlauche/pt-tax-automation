from __future__ import annotations

import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import requests
import questionary
from currency_converter import CurrencyConverter, ECB_URL
from dotenv import load_dotenv
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


DESCRIPTIONS = {
    'teaching': 'Serviços de ensino a distancia',
    'website build': 'Construção de website',
    'automation': 'Serviços de automação de pagina web',
}


# Collect details of the invoice

class Invoice(BaseModel):
    amount: Decimal
    currency: str = 'USD'
    date: date
    client_name: str
    description: str

    @classmethod
    def from_input(cls,
                   client_name: str | None = None,
                   amount: Decimal | None = None,
                   date: date | None = None,
                   description: str | None = None,
                   ) -> Invoice:
        client_name = client_name or input('Enter the full name of the client: ')
        amount = amount or input('Enter the invoice amount in USD: $')
        date = date or input('Enter the date (format: YYYY-MM-DD): ')
        description = input(f'Enter the description (leave blank to choose): ')
        if not description:
            option = questionary.select(
                'What service did you provide?',
                choices=DESCRIPTIONS.keys()
            ).ask()
            description = DESCRIPTIONS[option]
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
    exchange_rates_dir = Path('exchange_rates').resolve()
    exchange_rates_dir.mkdir(exist_ok=True)
    # 1. Get the latest exchange rates
    exchange_rates_file = exchange_rates_dir / f'ecb_{datetime.today().date():%Y%m%d}.zip'
    if not exchange_rates_file.exists():
        response = requests.get(ECB_URL)
        with exchange_rates_file.open('wb') as f:
            f.write(response.content)

    # 2. Convert the amount to EUR
    amount = CurrencyConverter(str(exchange_rates_file)).convert(amount, from_currency, to_currency, date)
    return amount


# Submit the invoice to the client
class TaxPortalWebsite:
    URLS = {
        'login': 'https://www.acesso.gov.pt/v2/loginForm?partID=SIRE&path=/recibos/portal/',
        'login success': 'https://irs.portaldasfinancas.gov.pt/recibos/;sireinter_JSessionID=',
        'invoice start': 'https://irs.portaldasfinancas.gov.pt/recibos/portal/emitir/emitirDocumentos',
        'invoice form': 'https://irs.portaldasfinancas.gov.pt/recibos/portal/emitir/emitirfatura',
        'invoice complete': 'https://irs.portaldasfinancas.gov.pt/recibos/portal/consultar/detalhe/',
    }

    def __init__(self, login: bool = True, headless: bool = False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        self.browser = webdriver.Chrome()
        if login:
            self.login()

    def login(self):
        self.browser.get(self.URLS['login'])
        load_dotenv()
        nif = os.getenv('NIF')
        tax_portal_password = os.getenv('TAX_PORTAL_PASSWORD')
        tab_labels = self.browser.find_elements('css selector', '.tab-label')
        tab_labels[1].click()
        self.browser.find_element('id', 'username').send_keys(nif)
        self.browser.find_element('id', 'password-nif').send_keys(tax_portal_password)
        self.browser.find_element('id', 'sbmtLogin').click()
        WebDriverWait(self.browser, 10).until(EC.url_contains(self.URLS['login success']))

    def submit_invoice(self, invoice: Invoice, confirm: bool = True):
        if not invoice.currency == 'EUR':
            invoice = invoice.to_currency('EUR')
        invoice_form_url = f'{self.URLS["invoice form"]}?dataCopia={invoice.date:%Y-%m-%d}&tipoRecibo=FR'
        self.browser.get(invoice_form_url)
        Select(self.browser.find_element('css selector', 'select[name="pais"]')).select_by_visible_text('ESTADOS UNIDOS')
        self.browser.find_element('css selector', 'input[name="nomeAdquirente"]').send_keys(invoice.client_name)
        self.browser.find_element('css selector', 'input[name="titulo"][value="1"]').click()
        self.browser.find_element('css selector', 'textarea[name="servicoPrestado"]').send_keys(invoice.description)
        self.browser.find_element('css selector', 'input[name="valorBase"]').send_keys(f'{invoice.amount:.2f}')
        Select(self.browser.find_element('css selector', 'select[name="regimeIva"]')).select_by_visible_text('Regras de localização - art.º 6.º [regras especificas]')
        Select(self.browser.find_element('css selector', 'select[name="regimeIncidenciaIrs"]')).select_by_visible_text('Sem retenção - Não residente sem estabelecimento')
        if confirm:
            input('Review the invoice and press Enter to confirm...')
        issue_button = [button for button in self.browser.find_elements('css selector', 'button') if button.text == 'EMITIR'][0]
        issue_button.click()
        if confirm:
            input('Review one last time and press Enter to confirm...')
        WebDriverWait(self.browser, 10).until(EC.visibility_of_any_elements_located(('css selector', 'button.btn-success')))
        final_submit_button = [button for button in self.browser.find_elements('css selector', 'button.btn-success') if button.text == 'EMITIR'][0]
        final_submit_button.click()
        WebDriverWait(self.browser, 10).until(EC.url_contains(self.URLS['invoice complete']))
        if confirm:
            input('Invoice submitted successfully. Press Enter to exit...')
