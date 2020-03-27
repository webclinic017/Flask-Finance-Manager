from webApp import create_app , db
from webApp.models import Transaction
from sqlalchemy import extract
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import math
app = create_app()
app.app_context().push()



#to use engine access by db.engine so you can convert to pandas to plot


trans = pd.read_sql_table("transaction",  con=db.engine)

# #this can be used to plot the pie chart using the categories as labels 
# pie_1.plot.pie(labels=pie_1.index , autopct='%1.1f%%')

def generate_report(begin,end,df):
    #makes the index the date column so we can use slicing
    df.set_index('date', inplace=True)
    data = df[begin:end]
    data_grp = data.groupby(['category'])
    sums = data_grp.apply(lambda x: x.amount.sum())
    info= {}
    info['sums'] = sums
    info['total_sum'] = sum(info['sums'])
    return sums

a= generate_report('2020', '2021', trans)

def num_month(begin,end):
    #Using a sting of format %Y-%m-%d calculates the number of months rounded up
    begin = dt.datetime.strptime(begin, '%Y-%m-%d')
    end = dt.datetime.strptime(end, '%Y-%m-%d')
    return math.ceil((end - begin).days/30)
    
    
t=num_month('2020-02-04','2020-05-05')
