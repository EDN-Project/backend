from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
import psycopg2
import random
import smtplib
import bcrypt
import jwt
import secrets
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import threading
import pandas as pd


# -------------------------------- vars for global analysis ------------------------------------- 

month = 0
code = 0
country = 0
variety = 0
countries = []

recommendations = {
    "Elsanta": "Increase potassium (K) to 3:1:4 and reduce irrigation at the end of fruiting to enhance Brix levels.",
    "Camarosa": "Maintain NPK at 2:1:3 and increase light exposure to 16 hours per day to boost photosynthesis.",
    "Albion": "Use NPK at 1:2:3 and increase calcium (Ca) to 250 ppm to prevent fibrosis and enhance sweetness.",
    "Charlotte": "Maintain balanced fertilization at 1:2:3 and increase magnesium (Mg) to support sugar production.",
    "Monterey": "Reduce nitrogen (N) after flowering to 1:1:3 and increase irrigation and light during early fruiting.",
    "San Andreas": "Use 2:1:3 and increase iron (Fe) to 0.2 ppm to enhance color and flavor.",
    "Seolhyang": "Naturally high in sugar, so focus on high-potassium fertilization (1:2:4) and gradually reduce irrigation.",
    "Gariguette": "Keep NPK at 1:3:2 and increase zinc (Zn) to 0.1 ppm to enhance taste and sweetness.",
    "Elan": "Requires high phosphorus (P) levels; use 1:3:3 to improve color and taste.",
    "Jewel": "Use 1:2:4 and increase boron (B) to 0.1 ppm to improve fruit quality.",
    "Tochiotome": "Increase magnesium (Mg) to 80 ppm and reduce nitrogen after flowering to enhance sugar levels.",
    "Festival": "Use 1:2:3 and decrease irrigation during the last two weeks of fruiting to concentrate sugar."
}


# ----------------------------------vars for sign up and authentification---------------------------------


user_id = 0


# -----------------------------------------all things about the app-------------------------------------------------





app = Flask(__name__)
CORS(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = secrets.token_hex(16) 
app.config['SESSION_PERMANENT'] = True 
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

Session(app)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = "275610438837-170leviano6ajrmtlocod0q7an5ce07u.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "http://127.0.0.1:5000/auth/google/callback"

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


# -----------------------------------------------connection to the database------------------------------------------------------------


# بيانات الاتصال بقاعدة البيانات
connection_string = "dbname=eden user=postgres password=ahmed2003 host=db port=5432"
conn = psycopg2.connect(connection_string)

#make host = localhost if you want to run it locally not from the container
