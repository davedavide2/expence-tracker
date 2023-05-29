from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQLdb
import datetime

app = Flask(__name__)
app.secret_key = 'davide271'

# Connection function
def connection():
    try:
        conn = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="",  
            db="expense_tracker_db"
        )
        return conn
    except MySQLdb.Error as e:
        print("Connection error:", e)
        return None
    
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = connection()
        cursor = conn.cursor()
        
        # Check if the username and password match a user in the database
        query = "SELECT * FROM users_tbl WHERE USERNAME = %s AND PASSWORD = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            session['ID'] = user[0]  # Store the user ID in the session
            return redirect('/dashboard')  # Redirect to the dashboard page
        else:
            error = 'Invalid username or password. Please try again.'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = connection()
        cursor = conn.cursor()
        
        # Check if the username is already taken
        query = "SELECT * FROM users_tbl WHERE USERNAME = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            error = 'Username already exists. Please choose a different username.'
            return render_template('login.html', error=error)
        
        # Insert the new user into the database
        query = "INSERT INTO users_tbl (USERNAME, PASSWORD, EMAIL) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, email))
        conn.commit()
        
        # Redirect to the login page after successful signup
        return redirect('/login')
    
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in by verifying the presence of 'ID' in the session
    if 'ID' in session:
        user_id = session['ID']
        conn = connection()
        cursor = conn.cursor()

        # Fetch the user information from the database
        query = "SELECT * FROM users_tbl WHERE ID = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        # Fetch the expenses for the current user
        query = "SELECT * FROM expense_tbl WHERE USER_ID = %s"
        cursor.execute(query, (user_id,))
        expenses = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('dashboard.html', user=user, expenses=expenses,)

    # If the user is not logged in, redirect to the login page
    return redirect('/login')


@app.route('/expense_history')
def history():
    # Get the current date
    today = datetime.date.today()

    # Calculate the start date of the previous month
    start_date = datetime.date(today.year, today.month - 1, 1)

    # Calculate the end date of the previous month
    if today.month == 1:
        end_date = datetime.date(today.year - 1, 12, 31)
    else:
        end_date = datetime.date(today.year, today.month - 1, today.day)

    # Move expenses from current month to expense_history_tbl
    conn = connection()
    cursor = conn.cursor()
    move_query = "INSERT INTO expense_history_tbl (H_AMOUNT, H_DESCRIPTION, H_CATEGORY, H_DATE) SELECT amount, description, category, date FROM expense_tbl WHERE date >= %s AND date <= %s"
    cursor.execute(move_query, (start_date, end_date))

    # Delete expenses from current month
    delete_query = "DELETE FROM expense_tbl WHERE date >= %s AND date <= %s"
    cursor.execute(delete_query, (start_date, end_date))

    conn.commit()
    cursor.close()
    conn.close()

    # Retrieve the expenses from the expense_history_tbl
    conn = connection()
    cursor = conn.cursor()
    history_query = "SELECT * FROM expense_history_tbl"
    cursor.execute(history_query)
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    # Pass the expenses to the history page template
    return render_template('expense_history.html', expenses=expenses)




# Logout route
@app.route('/logout')
def logout():
    # Clear the user_id from the session
    session.pop('ID', None)
    return redirect('/login')

#<--------------------------------------------------------USER CONTROL SESSION------------------------------------------------------------------->

@app.route('/update_income', methods=['POST'])
def update_income():
    if 'ID' in session:
        user_id = session['ID']
        user_income = request.form['user_income']
        
        # Update the user's monthly income in the database
        conn = connection()
        cursor = conn.cursor()
        query = "UPDATE users_tbl SET INCOME = %s WHERE ID = %s"
        cursor.execute(query, (user_income, user_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect('/dashboard')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        category = request.form['category']
        date = request.form['date']
        user_id = session['ID']

        conn = connection()
        cursor = conn.cursor()

        try:
            query = "INSERT INTO expense_tbl (USER_ID, AMOUNT, DESCRIPTION, CATEGORY, DATE) VALUES (%s, %s, %s, %s, %s)"
            values = (user_id, amount, description, category, date)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            cursor.close()
            conn.close()
            return "Error adding expense: " + str(e)
    else:
        # Handle GET request for rendering the form
        return render_template('add_expense.html')
    

@app.route('/modify_expense/<expense_id>', methods=['GET', 'POST'])
def modify_expense(expense_id):
    conn = connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Handle the form submission and update the expense in the database
        amount = request.form['amount']
        description = request.form['description']
        category = request.form['category']
        date = request.form['date']

        try:
            query = "UPDATE expense_tbl SET AMOUNT = %s, DESCRIPTION = %s, CATEGORY = %s, DATE = %s WHERE EXPENSE_ID = %s"
            values = (amount, description, category, date, expense_id)
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            cursor.close()
            conn.close()
            return "Error modifying expense: " + str(e)
    else:
        # Fetch the expense details from the database
        query = "SELECT * FROM expense_tbl WHERE EXPENSE_ID = %s"
        cursor.execute(query, (expense_id,))
        expense = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template('modify_expense.html', expense=expense)

@app.route('/delete_expense/<int:expense_id>', methods=['GET', 'POST'])
def delete_expense(expense_id):
    if request.method == 'POST':
        conn = connection()
        cursor = conn.cursor()

        try:
            query = "DELETE FROM expense_tbl WHERE EXPENSE_ID = %s"
            cursor.execute(query, (expense_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            cursor.close()
            conn.close()
            return "Error deleting expense: " + str(e)
    else:
        return render_template('delete_expense.html', expense_id=expense_id)


@app.route('/expense_overview')
def expense_overview():
    # Check if the user is logged in by verifying the presence of 'ID' in the session
    if 'ID' in session:
        user_id = session['ID']
        conn = connection()
        cursor = conn.cursor()

        # Fetch the user information from the database
        query = "SELECT * FROM users_tbl WHERE ID = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        # Fetch the expenses for the current user
        query = "SELECT * FROM expense_tbl WHERE USER_ID = %s"
        cursor.execute(query, (user_id,))
        expenses = cursor.fetchall()

        # Calculate the total amount of expenses
        total_amount = sum(expense[2] for expense in expenses)

        # Check if the monthly income is empty
        if user[5] is not None and user[5] != "":
            has_income = True
            monthly_income = user[5]
        else:
            has_income = False
            monthly_income = 0

        # Calculate the remaining balance
        if monthly_income is not None:
            remaining_balance = monthly_income - (total_amount if total_amount else 0)
        else:
            remaining_balance = 0

        cursor.close()
        conn.close()

        return render_template('expense_overview.html', user=user, expenses=expenses, total_amount=total_amount, has_income=has_income, monthly_income=monthly_income, remaining_balance=remaining_balance)



    # If the user is not logged in, redirect to the login page
    return redirect('/login')



@app.route('/chartcomparison')
def chartcomparison():
    return render_template('chartcomparison.html')

@app.route('/homepage')
def home_page():
    return render_template('home_page.html')

if __name__ == '__main__':
    app.run(debug=True, port=3390)

    

