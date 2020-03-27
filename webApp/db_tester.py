from webApp import create_app , db
from webApp.models import Transaction , Income
from sqlalchemy import extract
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import math
app = create_app()
app.app_context().push()



#to use engine access by db.engine so you can convert to pandas to plot

#trans = pd.read_sql_table("transaction",  con=db.engine)

df = pd.read_sql_table("income",  con=db.engine)
info = {}
info['amount'] = df['amount'].sum()
info['VAT'] = (info['amount']/121)*21
info['net'] = info['amount'] - info['VAT']