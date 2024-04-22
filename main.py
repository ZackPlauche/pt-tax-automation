from tax_automation import Invoice, TaxPortalWebsite


invoice = Invoice(
    amount=100,
    currency='USD',
    date='2024-04-19',
    client_name='Kenneth Lepping',
    description='Work done for client'
)

TaxPortalWebsite().submit_invoice(invoice, submit=False)