from flask import render_template, url_for, flash, redirect, request, Blueprint , make_response
from flask_login import login_user, current_user, logout_user, login_required
from webApp import db, bcrypt
from webApp.models import User, Post , Task , Transaction , Income
from webApp.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm, TaskForm, 
                                   Sort_TaskForm, TransactionForm, Sort_Transactions, 
                                   Generate_Report, IncomeForm)
from webApp.users.utils import save_picture, send_reset_email
import datetime as dt
from sqlalchemy import extract
import matplotlib.pyplot as plt
import pandas as pd
import base64
import math
from io import BytesIO





users = Blueprint('users', __name__)


#Registration Page
@users.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username= form.username.data , email = form.email.data , password= hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register' , form=form)


#Login Page
@users.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccesful Please check email and password', 'danger')        
    return render_template('login.html', title='Login' , form=form)

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))    


@users.route('/account', methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!','success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static' , filename= 'profile_pics/' + current_user.image_file) 
    return render_template('account.html',title='Account',
                           image_file=image_file , form=form)


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page' , 1 , type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page , per_page = 5)
    return render_template('user_posts.html',posts=posts , user=user )


@users.route("/reset_password" , methods=['GET','POST'] )
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form= RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your Password', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title = 'Reset Password' , form=form)

@users.route("/reset_password/<token>" , methods=['GET','POST'] )
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)    
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been changed')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title = 'Reset Password' , form=form)                

#TASK SECTION


@users.route("/tasks" , methods=['GET','POST'] )
@login_required
def tasks():
    form = TaskForm()
    sort_form= Sort_TaskForm()
    tasks = Task.query.filter_by(author = current_user).order_by(Task.date_posted.desc())

    if form.submit.data and form.validate_on_submit():
        task = Task(category= form.category.data, content=form.content.data, author= current_user, due_date=form.due_date.data , importance = int(form.importance.data))
        print(task)
        db.session.add(task)
        db.session.commit()
        flash('Task Added!','success')
        return redirect(url_for('users.tasks'))

    if sort_form.sort_submit.data and sort_form.validate_on_submit():
        return redirect(url_for('users.sort_tasks', category=sort_form.sort_category.data, date_desc=sort_form.date_desc.data , imp_desc=sort_form.imp_desc.data))
        
    return render_template('tasks.html',title='To-do List' , form=form, tasks=tasks ,sort_form=sort_form , no_sidebar=True)


@users.route("/tasks/<string:category><date_desc><imp_desc>", methods=['GET','POST'])
@login_required
def sort_tasks(category, date_desc=None, imp_desc=None):
    form = TaskForm()
    sort_form = Sort_TaskForm()
    if sort_form.sort_submit.data and sort_form.validate_on_submit():
        return redirect(url_for('users.sort_tasks', category=sort_form.sort_category.data, date_desc=sort_form.date_desc.data , imp_desc=sort_form.imp_desc.data))
    

    if category == 'all':
        if date_desc == '1':
            tasks = Task.query.filter_by(author = current_user).order_by(Task.date_posted.desc())
        elif imp_desc == '1':
            tasks = Task.query.filter_by(author = current_user).order_by(Task.importance.desc())
        else:
            tasks = Task.query.filter_by(author = current_user)
    else:        
        if date_desc == '1':
            tasks = Task.query.filter_by(author = current_user , category = category).order_by(Task.date_posted.desc())
        elif imp_desc == '1':
            tasks = Task.query.filter_by(author = current_user , category = category).order_by(Task.importance.desc())
        else:
            tasks = Task.query.filter_by(author = current_user , category = category)

    return render_template('tasks.html', title='To-do List' , form=form, tasks=tasks , sort_form=sort_form , no_sidebar=True)


@users.route("/task/<int:task_id>/delete", methods=['POST'])
@login_required
def delete_task(task_id):
    task= Task.query.get_or_404(task_id)
    if task.author != current_user:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash('Task completed!', 'success')
    return redirect(request.referrer)


#Finance Section ---------------------------------------------------------------------------------------------------------------------------------------------------

#Functions
def calc_TAX(amount,per):
    return amount/(100+per)*per

def sum_total(transactions):
    return sum([trans.amount for trans in transactions])



#Filters by month and year
# trans = Transaction.query.filter(extract("month", Transaction.date)==month).filter(extract('year', Transaction.date)==year).all()

curr_month= dt.date.today().strftime("%m")


#Transaction Page where you can add and sort transactions by category and month

@users.route("/transactions/", methods=['GET','POST'])
@login_required
def transactions():
    form = TransactionForm()
    sort_form = Sort_Transactions()
    #Gets querystring arguments if none set to a default
    if request.args.get("month"):
        month = request.args.get("month")
    else:
        month = curr_month

    if request.args.get("category"):
        category = request.args.get("category")
    else:
        category = "all"


    if sort_form.sort_submit.data and sort_form.validate_on_submit():
        return redirect(url_for('users.transactions', month=sort_form.month.data, category=sort_form.sort_category.data,  date_desc=sort_form.date_desc.data))

    if category == 'all':
        transactions = Transaction.query.filter_by(author = current_user).filter(extract("month", Transaction.date)==month).all()
        total_sum = sum_total(transactions)    
    else:        
        transactions = Transaction.query.filter_by(author = current_user , category = category).filter(extract("month", Transaction.date)==month).all()
        total_sum = sum_total(transactions)


    #Adds Transaction to the database
    if form.submit.data and form.validate_on_submit():

        tax= calc_TAX(float(form.amount.data),float(form.tax_percentage.data))
        if form.category.data == 'abbonement':
            transaction = Transaction(category= form.category.data, 
            content=form.content.data, author= current_user, 
            amount=float(form.amount.data) , tax_percentage = float(form.tax_percentage.data) , tax_amount=tax, sub=True)
        else:
            transaction = Transaction(category= form.category.data, 
            content=form.content.data, author= current_user, 
            amount=float(form.amount.data) , tax_percentage = float(form.tax_percentage.data) , tax_amount=tax)
        db.session.add(transaction)
        db.session.commit()
        flash('Added!','success')
        return redirect(url_for('users.transactions', month=curr_month, category="all",  date_desc=0))



    return render_template('transactions.html', title='Finances' , form=form,  transactions=transactions , sort_form=sort_form , total_sum=total_sum, no_sidebar=True , curr_month=curr_month)



#Deletes a Transaction
@users.route("/transaction/<int:transaction_id>/delete", methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction= Transaction.query.get_or_404(transaction_id)
    if transaction.author != current_user:
        abort(403)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted!', 'success')
    return redirect(request.referrer)



#Add income
@users.route("/add_income", methods=['GET','POST'])
@login_required
def add_income():
    form = IncomeForm()
    if form.submit.data and form.validate_on_submit():
        if form.monthly.data == "Yes":
            monthly = True
        else:
            monthly = False

        income = Income(author= current_user , company = form.company.data , source = form.source.data , amount = form.amount.data , monthly = monthly , hours_worked = form.hours_worked.data)
        db.session.add(income)
        db.session.commit()
        flash('Income Added!','success')
        return redirect(url_for('users.add_income'))

    return render_template('add_income.html', form=form)




#Dashboard 

@users.route("/dashboard/<begin>/<end>", methods=['GET','POST'])
@login_required
def dashboard(begin,end):



    #Gets all users transactions 
    trans = Transaction.query.filter_by(author = current_user)
    

    #Checks if the current user has any transactions otherwise redirects the user to the transaction page
    if trans.count() != 0 :
        #Transform transactions into a dataframe with the date as index
        df = pd.DataFrame(vars(t) for t in trans)
        df.set_index('date', inplace= True)

        #Form for setting begin and end date
        form = Generate_Report()
        if form.submit.data and form.validate_on_submit():
            return redirect(url_for('users.dashboard',begin = form.begin.data, end= form.end.data))

        #Converts begin and end to datetime objects
        begin = dt.datetime.strptime(begin, '%Y-%m-%d')
        end = dt.datetime.strptime(end, '%Y-%m-%d')

        #filters out the fixed monthly costs
        filt = (df['sub'] == False)
        data = df.loc[filt][begin:end]
        data_grp = data.groupby(['category'])
        sums = data_grp.apply(lambda x: x.amount.sum())
        #Dict containing all info so we can pass this onto the template
        expenses = {}
        expenses['sums'] = sums
        expenses['total_sum'] = sum(expenses['sums'])
        expenses['monthly_cost'] = df.loc[df['sub'] == True, 'amount'].sum()

        #Calculates total monthly cost by subtracting end and begin taking the days and rounding the days/29 up to the nearest integer
        expenses['total_monthly_cost'] = expenses['monthly_cost']*math.ceil((end-begin).days/29)
        expenses['total'] = expenses['total_monthly_cost'] + expenses['total_sum']

        
        expenses['begin_month'] = begin.strftime('%B %Y')
        expenses['end_month'] = end.strftime('%B %Y')


                #Generates Graph
        # Generate the figure **without using pyplot**.
        fig = plt.figure()
        ax = fig.subplots()
        ax.pie(sums.values, shadow=True , startangle=90, labels=sums.index, autopct='%1.1f%%')
        # Save it to a temporary buffer.
        buf = BytesIO()
        fig.savefig(buf, format="png")
        # Embed the result in the html output.
        png_data = base64.b64encode(buf.getbuffer()).decode("ascii")


        #Income data
        income_data = Income.query.filter_by(author = current_user)
        income_df = pd.DataFrame(vars(i) for i in income_data)
        income_df.set_index('date', inplace= True)

        income_df_slice = income_df[begin:end]

        income = {}

        freelance_df = income_df.loc[(income_df_slice['source'] == 'Freelance')]
        income['freelance'] = {}
        income['freelance']['amount'] = freelance_df['amount'].sum()
        income['freelance']['VAT'] = (income['freelance']['amount']/121)*21
        income['freelance']['net_amount'] = income['freelance']['amount'] - income['freelance']['VAT'] 
        income['freelance']['hours_worked'] = freelance_df['hours_worked'].sum()
        income['freelance']['avg_wage'] =  income['freelance']['net_amount']/income['freelance']['hours_worked']
        income['freelance']['avg_hours'] = float(income['freelance']['hours_worked'])/((end-begin).days/30.44)

        wage_df = income_df.loc[(income_df_slice['source'] == 'Wage')]    
        income['wage'] = {}
        income['wage']['amount'] = wage_df['amount'].sum()
        income['wage']['hours_worked'] = wage_df['hours_worked'].sum()
        income['wage']['avg_hours'] = float(income['wage']['hours_worked'])/((end-begin).days/30.44)


        income['other'] = {}
        income['other']['monthly'] = income_df.loc[(income_df['monthly'] == True)]['amount'].sum()
        income['other']['total_monthly'] = income['other']['monthly']*math.ceil((end-begin).days/29)
        income['other']['amount'] = income_df_slice.loc[(income_df_slice['source'] == 'Other')]['amount'].sum()

        income['total'] = income['freelance']['net_amount'] + income['wage']['amount'] + income['other']['total_monthly'] + income['other']['amount']

        total = income['total'] - expenses['total']

        return render_template('dashboard.html' , title='Dashboard' , expenses=expenses , income=income , total=total, form=form , data=png_data , no_sidebar=True)   
    else:
        flash("Please add some transactions first before accessing the dashboard",'danger')
        return redirect(url_for('users.transactions', month=curr_month, category="all", date_desc=0))








# END FINANCE SECTION -----------------------------------------------------------------------
