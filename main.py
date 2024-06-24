from tax_automation import Invoice, TaxPortalWebsite, DESCRIPTIONS

default_description = DESCRIPTIONS['automation']

invoice = Invoice.from_input(description=default_description)
TaxPortalWebsite().submit_invoice(invoice, confirm=True)
input('Press enter to end')
