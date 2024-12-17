import unittest
from main import app, db, User, Transaction
from werkzeug.security import generate_password_hash
from datetime import datetime

class BankingAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client and initialize the test database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

            # Create a test user
            hashed_password = generate_password_hash("testpassword", method='pbkdf2:sha256')
            test_user = User(username="testuser", email="test@example.com",
                             password=hashed_password, phone_number="1234567890",
                             account_number="AC12345678", balance=100.0)
            db.session.add(test_user)
            db.session.commit()

    def tearDown(self):
        """Clean up the database after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        """Helper function to log in a user."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_register_user(self):
        """Test user registration."""
        response = self.client.post('/register', data=dict(
            username="newuser",
            password="newpassword",
            email="newuser@example.com",
            phone_number="0987654321"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created successfully!', response.data)

    def test_login_successful(self):
        """Test successful user login."""
        response = self.login("testuser", "testpassword")
        self.assertIn(b'Logged in successfully!', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.login("testuser", "wrongpassword")
        self.assertIn(b'Invalid username or password.', response.data)

    def test_deposit(self):
        """Test deposit functionality."""
        self.login("testuser", "testpassword")
        response = self.client.post('/deposit', data=dict(amount=50), follow_redirects=True)
        self.assertIn(b'Deposited $50.0 successfully!', response.data)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            self.assertEqual(user.balance, 150.0)  # 100 initial + 50 deposit

    def test_withdraw_successful(self):
        """Test successful withdrawal."""
        self.login("testuser", "testpassword")
        response = self.client.post('/withdraw', data=dict(amount=50), follow_redirects=True)
        self.assertIn(b'Withdrew $50.0 successfully!', response.data)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            self.assertEqual(user.balance, 50.0)  # 100 initial - 50 withdraw

    def test_withdraw_insufficient_funds(self):
        """Test withdrawal with insufficient funds."""
        self.login("testuser", "testpassword")
        response = self.client.post('/withdraw', data=dict(amount=200), follow_redirects=True)
        self.assertIn(b'Insufficient funds.', response.data)

    def test_transfer_successful(self):
        """Test successful fund transfer."""
        with app.app_context():
            # Create a recipient user
            recipient_user = User(username="recipient", email="recipient@example.com",
                                  password=generate_password_hash("password"), phone_number="9876543210",
                                  account_number="AC87654321", balance=50.0)
            db.session.add(recipient_user)
            db.session.commit()

        self.login("testuser", "testpassword")
        response = self.client.post('/transfer', data=dict(
            recipient="recipient",
            recipient_account_number="AC87654321",
            amount=30
        ), follow_redirects=True)
        self.assertIn(b'Transferred $30.0 to recipient successfully!', response.data)

        with app.app_context():
            sender = User.query.filter_by(username="testuser").first()
            recipient = User.query.filter_by(username="recipient").first()
            self.assertEqual(sender.balance, 70.0)  # 100 - 30
            self.assertEqual(recipient.balance, 80.0)  # 50 + 30

    def test_transfer_invalid_recipient(self):
        """Test transfer to an invalid recipient."""
        self.login("testuser", "testpassword")
        response = self.client.post('/transfer', data=dict(
            recipient="nonexistent",
            recipient_account_number="AC99999999",
            amount=30
        ), follow_redirects=True)
        self.assertIn(b'Recipient not found or account number mismatch.', response.data)

    def test_transaction_history(self):
        """Test transaction history page."""
        self.login("testuser", "testpassword")
        response = self.client.get('/transaction_history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Transaction ID', response.data)

    def test_download_transactions(self):
        """Test downloading transactions as an Excel file."""
        self.login("testuser", "testpassword")
        response = self.client.get('/download_transactions')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == '__main__':
    unittest.main()
