from flask import Flask, render_template, request, redirect, url_for
from mysql import connector
from datetime import datetime

app = Flask(__name__)

# Connect to MySQL database
db = connector.connect(
    host='localhost',
    user='root',
    password='',
    database='library'
)

cursor = db.cursor()


@app.route('/')
def index():
    cursor.execute('SELECT * FROM books ORDER BY timesIssued DESC LIMIT 5')
    most_popular = cursor.fetchall()

    cursor.execute('SELECT * FROM books ORDER BY stockQty LIMIT 5')
    least_stock = cursor.fetchall()

    cursor.execute('SELECT * FROM customer ORDER BY total_trans DESC LIMIT 5')
    highest_paying = cursor.fetchall()

    cursor.execute('SELECT * FROM customer ORDER BY denda DESC LIMIT 5')
    highest_denda = cursor.fetchall()

    cursor.execute('SELECT SUM(stockQty) as total FROM books')
    total_books = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(denda) as total FROM customer')
    total_denda = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM customer')
    customer_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM books')
    total_titles = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_issues = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(cost) as total FROM transactions')
    total_amount = cursor.fetchone()[0]

    return render_template('admin/index.html', most_popular=most_popular, highest_paying=highest_paying,
                           total_books=total_books, total_customer=customer_count,
                           total_issues=total_issues, highest_denda=highest_denda,
                           least_stock=least_stock, total_amount=total_amount,
                           total_titles=total_titles, total_denda=total_denda,)


@app.route('/books')
def books():
    cursor.execute('SELECT * FROM books')
    all_books = cursor.fetchall()
    return render_template('admin/books.html', all_books=all_books)

@app.route('/add_books', methods=['GET', 'POST'])
def add_books():
    if request.method == 'POST':
        book_title = request.form['title']
        book_author = request.form['author']
        book_stockQty = request.form['stockQty']

        cursor.execute('INSERT INTO books (title, authors, stockQty ) VALUES (%s, %s, %s)',
                       (book_title, book_author, book_stockQty))
        db.commit()
        return redirect('/books')
    else:
        return render_template('admin/add_books.html')

@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    cursor.execute('SELECT * FROM books WHERE book_id = %s', (id,))
    bookq = cursor.fetchone()

    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        stockQty = request.form['stockQty']

        cursor.execute('UPDATE books SET title=%s, authors=%s, stockQty=%s WHERE book_id=%s',
                       (title, authors, stockQty, id))
        db.commit()
        return redirect('/books')
    else:
        return render_template('/admin/edit_book.html', book=bookq)

@app.route('/books/delete/<int:id>')
def delete_book(id):
    cursor.execute('DELETE FROM books WHERE book_id=%s', (id,))
    db.commit()
    return redirect('/books')



@app.route('/issue_book', methods=['GET', 'POST'])
@app.route('/issue_book/<int:id>', methods=['GET', 'POST'])
def issue_book(id=1):
    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        cust_id = int(request.form['cust_id'])

        cursor.execute('SELECT * FROM books WHERE book_id = %s', (book_id,))
        book = cursor.fetchone()

        cursor.execute('UPDATE books SET timesIssued = timesIssued + 1, stockQty = stockQty - 1 WHERE book_id = %s',
                       (book_id,))
        db.commit()

        cursor.execute('INSERT INTO transactions (book_id, cust_id) VALUES (%s, %s)', (book_id, cust_id))
        db.commit()

        return redirect('/return_issue')

    elif request.method == 'GET':
        return render_template('/admin/issue_book.html', id=id)
    else:
        return render_template('/admin/issue_book.html')

@app.route('/return_issue', methods=['GET', 'POST'])
def return_issue():
    cursor.execute('SELECT * FROM transactions')
    issued_books = cursor.fetchall()
    books_issued = []

    for book in issued_books:
        bi = []
        bi.append(book[0])  # trans_id
        bi.append(book[1])  # book_id

        cursor.execute('SELECT title FROM books WHERE book_id = %s', (book[1],))
        book_title = cursor.fetchone()[0]
        bi.append(book_title)

        bi.append(book[2])  # cust_id

        cursor.execute('SELECT name FROM customer WHERE cust_id = %s', (book[2],))
        cust_details = cursor.fetchone()[0]
        bi.append(cust_details)

        bi.append(book[3])  # cost
        date = book[5].date()
        bi.append(date)  # issue_date
        bi.append(book[4])  # status
        books_issued.append(bi)

    return render_template('admin/return_issue.html', issued_books=books_issued)

@app.route('/books/return/<int:id>', methods=['GET', 'POST'])
def return_book(id):
    if request.method == 'POST':
        cost_form = int(request.form['cost'])
        cust_id = int(request.form['cust_id'])

        cursor.execute('UPDATE transactions SET cost = %s WHERE trans_id = %s', (cost_form, id))
        cursor.execute('UPDATE transactions SET status = "closed" WHERE trans_id = %s', (id,))
        db.commit()

        cursor.execute('SELECT * FROM transactions WHERE trans_id = %s', (id,))
        book = cursor.fetchone()

        cursor.execute('SELECT * FROM customer WHERE cust_id = %s', (cust_id,))
        cust = cursor.fetchone()

        cursor.execute('UPDATE customer SET total_trans = total_trans + %s, denda = denda + %s WHERE cust_id = %s',
                       (cost_form, cost_form, cust_id))
        db.commit()

    return redirect('/return_issue')


@app.route('/customers')
def customers():
    cursor.execute('SELECT * FROM customer')
    all_customers = cursor.fetchall()
    return render_template('admin/customers.html', all_customers=all_customers)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']

        cursor.execute('INSERT INTO customer (name) VALUES (%s)', (name,))
        db.commit()
        return redirect('/customers')

    else:
        return render_template('admin/add_customer.html')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def update_customer(id):
    cursor.execute('SELECT * FROM customer WHERE cust_id = %s', (id,))
    cust = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']

        cursor.execute('UPDATE customer SET name = %s WHERE cust_id = %s', (name, id))
        db.commit()
        return redirect('/customers')
    else:
        return render_template('admin/edit_customer.html', customer=cust)

@app.route('/customers/delete/<int:id>')
def delete_customers(id):
    cursor.execute('DELETE FROM customer WHERE cust_id = %s', (id,))
    db.commit()
    return redirect('/customers')

@app.route('/customers/pay/<int:id>', methods=['GET', 'POST'])
def pay_dues(id):
    cursor.execute('SELECT * FROM customer WHERE cust_id = %s', (id,))
    cust = cursor.fetchone()

    if request.method == 'POST':
        due = int(request.form['due'])

        cursor.execute('UPDATE customer SET denda = denda - %s WHERE cust_id = %s', (due, id))
        db.commit()
        return redirect('/customers')
    else:
        return render_template('admin/pay_dues.html', customer=cust)


@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/sub-register')
def subReg():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        # Basic validation, you can add more checks based on your requirements
        if not username or not email or not password or not confirm_password:
            return 'All fields are required.'

        if password != confirm_password:
            return 'Passwords do not match.'

        # Store the user in the dummy database (you may want to use a database like SQLAlchemy)
        # users_db.append({'username': username, 'email': email, 'password': password})

        return f'Registration successful for {username}!'

        return redirect('auth/register.html')
    
@app.route('/forgot-password')
def forgotPassword():
    return render_template('auth/forgot-password.html')


if __name__ == '__main__':
    app.run(debug=True)
