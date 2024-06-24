import questionary
from tax_automation import Invoice, TaxPortalWebsite, DESCRIPTIONS


option = questionary.select(
    'What do you want to do?',
    choices=DESCRIPTIONS.keys()
).ask()
print(DESCRIPTIONS[option])