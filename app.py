from flask import Flask, render_template, request
from tax_automation import Invoice, TaxPortalWebsite, DESCRIPTIONS

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-automation', methods=['POST'])
def start_automation():
    request_data = request.form
    client_name = request_data['client_name']
    amount = request_data['amount']
    date = request_data['date']
    description = request_data['description']
    situation = request_data['situation']
    invoice = Invoice(amount=amount, date=date, client_name=client_name, description=description)
    TaxPortalWebsite().submit_invoice(invoice, confirm=True)
    return render_template('index.html')




if __name__ == '__main__':
    app.run(debug=True)