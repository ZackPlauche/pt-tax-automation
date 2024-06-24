from decimal import Decimal
from datetime import datetime, timedelta, date

import pytest

from tax_automation import convert_currency, Invoice, TaxPortalWebsite


@pytest.fixture
def invoice_data():
    return {
        'client_name': 'John Doe',
        'amount': '100',
        'date': '2024-04-19',
        'description': 'Work done for client'
    }


class TestInvoice:

    def test_collect_details(self, invoice_data):
        invoice = Invoice(**invoice_data)
        assert invoice.client_name == 'John Doe'
        assert invoice.amount == Decimal('100')
        assert invoice.date == date(2024, 4, 19)
        assert invoice.description == 'Work done for client'

    def test_convert_currency(self, invoice_data):
        initial_invoice = Invoice(**invoice_data)
        converted_invoice = initial_invoice.to_currency('EUR')
        assert initial_invoice.currency == 'USD'
        assert initial_invoice.amount == Decimal('100')
        assert converted_invoice.currency == 'EUR'
        assert converted_invoice.amount != initial_invoice.amount


def test_convert_currency():
    four_days_ago = datetime.now() - timedelta(days=4)
    currency = convert_currency(100, 'USD', 'EUR', four_days_ago)


class TestTaxPortalWebsite:

    @pytest.mark.skip(reason='Reduce number of requests. Confirmed to be working.')
    def test_login(self):
        website = TaxPortalWebsite(login=False)
        website.login()
