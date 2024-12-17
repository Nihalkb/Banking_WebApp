# Banking_WebApp

## 📋 Project Description  
This project is a **Flask-based RESTful API** that provides basic **user management functionalities**. It allows users to **register**, **log in**, **check their balance**, and **update their balance** securely. The project uses **SQLite** as the database and incorporates secure password hashing for user credentials.

---

## 🚀 Features  
- **User Registration:** Users can register by providing a username and password. Passwords are securely hashed before storage.  
- **User Login:** Users can log in using their username and password.  
- **Balance Check:** Users can query their balance at any time.  
- **Update Balance:** Users can add or deduct funds from their account balance.  
- **Secure Password Handling:** Utilizes `Werkzeug` for hashing and verifying passwords.  

---

## 🏗️ Technologies Used  
- **Flask:** Web framework for building the API.  
- **SQLAlchemy:** ORM for database interaction.  
- **SQLite:** Lightweight database for data storage.  
- **Werkzeug:** Password hashing and verification for user security.  
- **JSON:** Data communication format for API endpoints.  

---

## 🗂️ Project Structure 
-
    ```plaintext
        ├── app.py          # Main application file with routes and database setup
        ├── starchyui.db    # SQLite database file (auto-created)
        ├── README.md       # Project documentation
        └── requirements.txt # Dependencies file

---

## ⚙️ Installation
Follow these steps to set up and run the project locally:
1. Clone the Repository
bash
Copy code
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
2. Create a Virtual Environment (Optional but Recommended)
bash
Copy code
python -m venv venv
source venv/bin/activate  # On Linux/Mac
venv\Scripts\activate     # On Windows
3. Install Dependencies
bash
Copy code
pip install -r requirements.txt
4. Run the Application
bash
Copy code
python app.py
5. Initialize the Database
You can initialize the database by hitting this endpoint:
http
Copy code
GET http://127.0.0.1:5000/init-db

---

## 📝 Example UsageRegister a New User
http
Copy code
POST /register
Content-Type: application/json

{
    "username": "john_doe",
    "password": "securepassword123"
}
Log in as a User
http
Copy code
POST /login
Content-Type: application/json

{
    "username": "john_doe",
    "password": "securepassword123"
}
Check Balance
http
Copy code
GET /balance?username=john_doe
Update Balance
http
Copy code
PUT /update-balance
Content-Type: application/json

{
    "username": "john_doe",
    "amount": 50.5
}
