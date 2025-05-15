from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
import psycopg2
import random
import smtplib
import calendar
import bcrypt
import jwt
import secrets
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import threading
import pandas as pd
import os
import time



# -----------------------------------------all things about the app-------------------------------------------------





app = Flask(__name__)
CORS(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = secrets.token_hex(16) 
app.config['SESSION_PERMANENT'] = True 
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

app.secret_key =os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
Session(app)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = "275610438837-170leviano6ajrmtlocod0q7an5ce07u.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "http://127.0.0.1:5000/auth/google/callback"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

# بيانات إرسال البريد الإلكتروني
EMAIL_ADDRESS = "eden111055@gmail.com"
EMAIL_PASSWORD = "cwal ftyz xkzt ftgn"

temp_data = {}
# إعدادات البريد الإلكتروني
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "eden111055@gmail.com"
app.config['MAIL_PASSWORD'] = "cwal ftyz xkzt ftgn"

mail = Mail(app)


def hash_password(password):
    """ دالة لتشفير كلمة المرور """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode()  # تحويل الـ bytes إلى نص مشفر

def verify_password(password, hashed):
    """ دالة للتحقق من صحة كلمة المرور """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode())

def delete_temp_data(email, delay=300):
    """ دالة لحذف البيانات المؤقتة بعد مدة معينة """
    def delayed_delete():
        threading.Timer(delay, lambda: temp_data.pop(email, None)).start()

    threading.Thread(target=delayed_delete, daemon=True).start()


def generate_token(user_id):
    payload = {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def send_email(email, code):
    try:
        msg = MIMEText(f"Your verification code is: {code}")
        msg['Subject'] = "Verification Code"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [email], msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")


# -----------------------------------------------connection to the database------------------------------------------------------------


# بيانات الاتصال بقاعدة البيانات
connection_string = "dbname=eden user=postgres password=ahmed2003 host= db port=5432"
conn = psycopg2.connect(connection_string)
