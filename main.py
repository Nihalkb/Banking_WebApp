from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import pandas as pd
from flask import send_file
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banking_app.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False, default="Checking")
    status = db.Column(db.String(20), nullable=False, default="Active")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer,
                             db.ForeignKey('user.id'),
                             nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def __repr__(self):
        return f'<Transaction {self.amount} from {self.sender.username} to {self.recipient.username}>'

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']

        # Retrieve the last account number from the database
        last_user = User.query.order_by(User.id.desc()).first()
        if last_user and last_user.account_number.isnumeric():
            last_account_number = int(last_user.account_number[2:])
            next_account_number = f"AC{last_account_number + 1}"
        else:
            # Default account number if no user exists yet
            next_account_number = f"AC{random.randint(10000000, 19999999)}"

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create a new user
        new_user = User(username=username,
                        password=hashed_password,
                        email=email,
                        phone_number=phone_number,
                        account_number=next_account_number,
                        balance=0)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        user = User.query.get(session['user_id'])
        user.balance += amount
        db.session.commit()
        flash(f'Deposited ${amount} successfully!')
        return redirect(url_for('dashboard'))

    return render_template('deposit.html')


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        user = User.query.get(session['user_id'])
        if user.balance >= amount:
            user.balance -= amount
            db.session.commit()
            flash(f'Withdrew ${amount} successfully!', 'success')
        else:
            flash('Insufficient funds.', 'warning')
        return redirect(url_for('dashboard'))

    return render_template('withdraw.html')



@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipient_username = request.form['recipient']
        recipient_account_number = request.form['recipient_account_number']
        amount = float(request.form['amount'])

        # Get the sender from the database
        sender = User.query.get(session['user_id'])
        # Get the recipient based on the username and account number
        recipient = User.query.filter_by(
            username=recipient_username,
            account_number=recipient_account_number).first()

        if not recipient:
            flash('Recipient not found or account number mismatch.', 'warning')
        elif sender.balance >= amount:
            # Deduct the amount from the sender
            sender.balance -= amount
            # Credit the amount to the recipient
            recipient.balance += amount

            # Log the transaction
            transaction = Transaction(sender_id=sender.id,
                                      recipient_id=recipient.id,
                                      amount=amount)
            db.session.add(transaction)

            # Commit the changes to the database
            db.session.commit()

            # Provide feedback to the user
            flash(
                f'Transferred ${amount} to {recipient_username} successfully!', 'success')

        else:
            flash('Insufficient funds.')

        return redirect(url_for('dashboard'))

    return render_template('transfer.html')

@app.route('/transaction_history', methods=['GET'])
def transaction_history():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id)
        | (Transaction.recipient_id == user.id)).all()

    # Render the transaction history page with the transaction data
    return render_template('transaction_history.html',
                           transactions=transactions)


@app.route('/download_transactions', methods=['GET'])
def download_transactions():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id)
        | (Transaction.recipient_id == user.id)).all()

    # Create a list of transactions to convert to DataFrame
    transaction_data = []
    for transaction in transactions:
        transaction_data.append({
            'Transaction ID':
            transaction.id,
            'Sender':
            transaction.sender.username,
            'Recipient':
            transaction.recipient.username,
            'Amount':
            transaction.amount,
            'Timestamp':
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Convert the transaction data to a DataFrame
    df = pd.DataFrame(transaction_data)

    # Create an in-memory Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaction History')
    output.seek(0)

    # Send the Excel file to the user
    return send_file(
        output,
        as_attachment=True,
        download_name=
        f"transaction_history_{user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
        mimetype=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == '__main__':
    app.run(debug=True)
