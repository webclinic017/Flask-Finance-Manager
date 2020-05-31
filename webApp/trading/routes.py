from flask import render_template, url_for, flash, redirect, request, Blueprint , make_response
from flask_login import login_user, current_user, logout_user, login_required
from webApp import db, bcrypt
from webApp.models import StockAlert

import ast


trading = Blueprint('trading', __name__)
@trading.route('/webhook', methods=['GET','POST'])
def webhook():
    if request.method == "POST":
        #Takes the webhook data as a string and converts it into dictionary
        data = ast.literal_eval(request.get_data(as_text=True))
        stockalert = StockAlert(high_price=data['price'], close_price= data['close'], low_price= data['low'] , exchange = data['exchange'], ticker=data['ticker'])
        db.session.add(stockalert)
        db.session.commit()

    alerts = StockAlert.query.all()    
    return render_template('webhook.html', alerts = alerts, no_sidebar=True)