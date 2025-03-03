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



recommendations = {
    "Elsanta": {
        "UK": "Increase potassium (K) to 3:1:4 for higher sweetness and reduce irrigation at the end of fruiting.",
        "Germany": "Maintain K at 2:1:3 for balanced taste and increase magnesium (Mg) to 50 ppm for better fruit quality.",
        "Netherlands": "Use 3:1:3 and increase light exposure to enhance color and firmness."
    },
    "Camarosa": {
        "Saudi Arabia": "Maintain NPK at 2:1:3, increase light to 16 hours per day, and boost potassium for a sweeter taste.",
        "Poland": "Adjust to 2:2:3, reduce potassium slightly to maintain mild acidity, and enhance phosphorus for flavor.",
        "USA": "Use 2:1:3, maintain balanced irrigation, and increase calcium to prevent soft fruit."
    },
    "Albion": {
        "France": "Use NPK at 1:2:3, increase calcium (Ca) to 250 ppm to enhance sweetness and firmness.",
        "Canada": "Maintain 1:2:4, boost boron (B) to 0.1 ppm for better fruit texture.",
        "Japan": "Use 1:3:3 to emphasize natural sweetness and enhance phosphorus levels."
    },
    "Monterey": {
        "UAE": "Reduce nitrogen (N) after flowering to 1:1:3 and increase potassium to improve sugar content.",
        "USA": "Increase irrigation and light during early fruiting for optimal development.",
        "Mexico": "Use 1:1:3, slightly increase magnesium for stronger fruit structure."
    },
    "San Andreas": {
        "Spain": "Use 2:1:3 and increase iron (Fe) to 0.2 ppm to enhance deep red color and sweetness.",
        "Italy": "Use 1:2:3 and increase calcium for firmer fruit.",
        "Brazil": "Adjust to 2:1:4, focusing on higher potassium for a more tropical sweetness."
    },
    "Seolhyang": {
        "South Korea": "Naturally sweet; focus on high-potassium fertilization (1:2:4) and gradually reduce irrigation.",
        "China": "Use 1:2:3, increase magnesium to 80 ppm to enhance sugar levels.",
        "Vietnam": "Maintain 1:2:4, increase boron to 0.1 ppm for better fruit uniformity."
    },
    "Gariguette": {
        "France": "Keep NPK at 1:3:2 and increase zinc (Zn) to 0.1 ppm for enhanced traditional taste.",
        "Belgium": "Use 1:2:3, increase phosphorus for richer aroma.",
        "Switzerland": "Use 1:3:3, adjust potassium for a refined sweetness."
    },
    "Elan": {
        "Netherlands": "Requires high phosphorus (P) levels; use 1:3:3 to improve color and taste.",
        "Sweden": "Use 1:3:2, increase magnesium to enhance aroma.",
        "Denmark": "Maintain 1:2:3, increase boron for better flowering."
    },
    "Jewel": {
        "USA": "Use 1:2:4 and increase boron (B) to 0.1 ppm for improved fruit quality.",
        "Canada": "Use 1:3:3 and increase calcium to enhance firmness.",
        "UK": "Maintain 1:2:3 and boost potassium for a balanced taste."
    },
    "Tochiotome": {
        "Japan": "Increase magnesium (Mg) to 80 ppm and reduce nitrogen after flowering to enhance sugar levels.",
        "South Korea": "Use 1:2:3 and maintain stable irrigation for a softer texture.",
        "China": "Increase potassium slightly to enhance sweetness."
    },
    "Festival": {
        "Egypt": "Use 1:2:3 and decrease irrigation during the last two weeks to concentrate sugar levels.",
        "Spain": "Maintain 1:2:3, increase calcium for improved firmness.",
        "USA": "Use 1:2:4, enhance potassium to intensify flavor."
    }
}





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
connection_string = "dbname=eden user=postgres password=ahmed2003 host= db port=5432"
conn = psycopg2.connect(connection_string)
