import pytest
from main import app, db, User, Transaction
from werkzeug.security import generate_password_hash
from datetime import datetime

# Pytest fixture to set up and tear down the Flask app and database
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for isolated tests
    app.config['SECRET_KEY'] = 'test_secret_key'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create a fresh database schema
            yield client
            db.session.remove()
            db.drop_all()  # Ensure the database is cleared after the test


# Helper function to create a test user
def create_user(username, email, phone_number, balance=1000):
    hashed_password = generate_password_hash("password", method="pbkdf2:sha256")
    user = User(username=username, email=email, password=hashed_password,
                phone_number=phone_number, account_number="AC12345678",
                balance=balance)
    db.session.add(user)
    db.session.commit()
    return user

# Test Index Route
def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the Banking App" in response.data

# Test User Registration
def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password',
        'phone_number': '1234567890'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created successfully!' in response.data

    user = User.query.filter_by(username='testuser').first()
    assert user is not None

# Test User Login
def test_login(client):
    create_user('loginuser', 'login@example.com', '9876543210')
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in successfully!' in response.data

# Test Dashboard Access
def test_dashboard(client):
    user = create_user('dashboarduser', 'dashboard@example.com', '1122334455')
    with client.session_transaction() as session:
        session['user_id'] = user.id

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Welcome, dashboarduser" in response.data

# Test Deposit Functionality
def test_deposit(client):
    user = create_user('deposituser', 'deposit@example.com', '1231231234', balance=500)
    with client.session_transaction() as session:
        session['user_id'] = user.id

    response = client.post('/deposit', data={'amount': '200'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Deposited $200.0 successfully!' in response.data

    user = User.query.get(user.id)
    assert user.balance == 700

# Test Withdraw Functionality
def test_withdraw(client):
    user = create_user('withdrawuser', 'withdraw@example.com', '3213213211', balance=500)
    with client.session_transaction() as session:
        session['user_id'] = user.id

    response = client.post('/withdraw', data={'amount': '200'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Withdrew $200.0 successfully!' in response.data

    user = User.query.get(user.id)
    assert user.balance == 300

# Test Insufficient Balance Withdrawal
def test_withdraw_insufficient(client):
    user = create_user('failwithdraw', 'failwithdraw@example.com', '5555555555', balance=100)
    with client.session_transaction() as session:
        session['user_id'] = user.id

    response = client.post('/withdraw', data={'amount': '200'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Insufficient funds.' in response.data

# Test Logout
def test_logout(client):
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged out successfully!' in response.data
