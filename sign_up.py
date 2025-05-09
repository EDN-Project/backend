
import app as a

def hash_password(password):
    """ دالة لتشفير كلمة المرور """
    salt = a.bcrypt.gensalt()
    hashed_password = a.bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode()  # تحويل الـ bytes إلى نص مشفر

def verify_password(password, hashed):
    """ دالة للتحقق من صحة كلمة المرور """
    return a.bcrypt.checkpw(password.encode('utf-8'), hashed.encode())

def delete_temp_data(email, delay=300):
    """ دالة لحذف البيانات المؤقتة بعد مدة معينة """
    def delayed_delete():
        a.threading.Timer(delay, lambda: a.temp_data.pop(email, None)).start()

    a.threading.Thread(target=delayed_delete, daemon=True).start()


def generate_token(user_id):
    payload = {'user_id': user_id, 'exp': a.datetime.utcnow() + a.timedelta(days=1)}
    return a.jwt.encode(payload, a.app.config['SECRET_KEY'], algorithm='HS256')


def generate_state():
    return ''.join(a.random.choices(a.string.ascii_letters + a.string.digits, k=16))


def send_email(email, code):
    try:
        msg = a.MIMEText(f"Your verification code is: {code}")
        msg['Subject'] = "Verification Code"
        msg['From'] = a.EMAIL_ADDRESS
        msg['To'] = email

        with a.smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(a.EMAIL_ADDRESS, a.EMAIL_PASSWORD)
            server.sendmail(a.EMAIL_ADDRESS, [email], msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")


@a.app.route("/")
def serve_json():
    return a.jsonify({"message": "EDEN!"})



@a.app.route('/register', methods=['POST'])
def register():
    data = a.request.json
    name, email, phone, password, company_name = (
        data.get('name'),
        data.get('email'),
        data.get('phone'),
        data.get('password'),
        data.get('company_name'),
    )

    try:
        cursor = a.conn.cursor()

        # ✅ التحقق مما إذا كان البريد الإلكتروني مسجلاً بالفعل
        cursor.execute("SELECT email FROM actor.user WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return a.jsonify({"error": "Email is already registered!"}), 400  # 🔹 إرجاع الخطأ مباشرة
        
        
        else:
        
            # ✅ تشفير كلمة المرور
            hashed_password = a.hash_password(password)

            # ✅ توليد كود التحقق (OTP)
            code = ''.join(a.random.choices('0123456789', k=6))

            # ✅ تخزين البيانات مؤقتًا
            a.temp_data[email] = {
                'name': name,
                'phone': phone,
                'password': hashed_password,
                'code': code,
                'company_name': company_name,
            }

            # ✅ إرسال كود التحقق عبر البريد الإلكتروني
            a.send_email(email, code)

            # ✅ حذف البيانات بعد 5 دقائق
            a.delete_temp_data(email)

            cursor.close()
            return a.jsonify({"message": "Verification code sent!"}), 200

    except Exception as e:
        return a.jsonify({"error": f"Registration failed: {e}"}), 500
    

@a.app.route('/confirm', methods=['POST'])
def confirm():
    data = a.request.json
    code = data.get('code')

    # البحث عن المستخدم بواسطة الكود فقط
    email = next((key for key, value in a.temp_data.items() if value['code'] == code), None)

    if email:
        user_data = a.temp_data[email]
        try:
            cursor = a.conn.cursor()
            cursor.execute("INSERT INTO actor.user (name, email, phone, password , company_name) VALUES (%s, %s, %s, %s , %s)",
                           (user_data['name'], email, user_data['phone'], user_data['password'] , user_data['company_name']))
            a.conn.commit()
            cursor.close()

            a.temp_data.pop(email)
            return a.jsonify({"message": "Registration successful!"}), 201
        except Exception as e:
            return a.jsonify({"error": f"Registration failed: {e}"}), 400

    return a.jsonify({"error": "Invalid or expired code!"}), 400


@a.app.route('/login', methods=['POST'])
def login():
    
    data = a.request.json
    email = data.get('email')
    password = data.get('password')

    try:
        cursor = a.conn.cursor()
        cursor.execute("SELECT user_id, password FROM actor.user WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return a.jsonify({"error": "User not found!"}), 404

        user_id, stored_password = user  # استرجاع ID وكلمة المرور المشفرة
        
        # ✅ التأكد أن `stored_password` نص صالح وليس `bytes`
        if isinstance(stored_password, bytes):
            stored_password = stored_password.decode('utf-8')
        
        # ✅ التحقق من كلمة المرور
        if a.bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            token = generate_token(user_id)
            
            return a.jsonify({"message": "Login successful!", "token": token}), 200
        else:
            return a.jsonify({"error": "Invalid password!"}), 401

    except Exception as e:
        print(f"❌ Error verifying password: {e}")
        return a.jsonify({"error": "Internal server error!"}), 500


@a.app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = a.request.get_json()
    user_email = data.get('email')

    if not user_email:
        return a.jsonify({'error': 'Email is required'}), 400

    try:
        cur = a.conn.cursor()
        cur.execute("SELECT user_id FROM actor.user WHERE email = %s", (user_email,))
        user = cur.fetchone()
        if not user:
            return a.jsonify({'error': 'User not found'}), 404

        reset_code = str(a.random.randint(100000, 999999))  # كود مكون من 6 أرقام
        a.temp_data[user_email] = reset_code  # تخزين الكود مؤقتًا

        # تشغيل الـ Timer لحذف الكود بعد 5 دقائق
        delete_temp_data(user_email)

        msg = a.Message(
            subject="Your Password Reset Code",
            sender=a.app.config['MAIL_USERNAME'],
            recipients=[user_email]
        )
        msg.body = f"Your password reset code is: {reset_code}. This code will expire in 5 minutes."

        a.mail.send(msg)
        return a.jsonify({"message": "Reset code sent!"}), 200

    except Exception as e:
        print("Error:", str(e))
        return a.jsonify({"error": "Failed to send email!"}), 500
    finally:
        cur.close()


@a.app.route('/reset-password', methods=['POST'])
def reset_password():
    data = a.request.get_json()
    user_email = data.get('email')
    reset_code = data.get('code')
    new_password = data.get('new_password')

    if not user_email or not reset_code or not new_password:
        return a.jsonify({'error': 'Missing required fields'}), 400

    if user_email not in a.temp_data or a.temp_data[user_email] != reset_code:
        return a.jsonify({'error': 'Invalid or expired code'}), 400

    try:
        cur = a.conn.cursor()
        hashed_password = a.bcrypt.hashpw(new_password.encode('utf-8'), a.bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE actor.user SET password = %s WHERE email = %s", (hashed_password, user_email))
        a.conn.commit()
        a.temp_data.pop(user_email, None)
        return a.jsonify({"message": "Password updated successfully!"}), 200

    except Exception as e:
        print("Error:", str(e))
        return a.jsonify({"error": "Failed to reset password!"}), 500
    finally:
        cur.close()

a.app.secret_key = a.os.urandom(24)
SCOPES = ["openid", "email", "profile"]


@a.app.route("/auth/google")
def auth_google():
    state = generate_state()  
    a.session["oauth_state"] = state  

    google = a.OAuth2Session(a.GOOGLE_CLIENT_ID, redirect_uri=a.REDIRECT_URI, scope=SCOPES, state=state)
    authorization_url, _ = google.authorization_url(a.GOOGLE_AUTH_URL)

    return a.redirect(authorization_url)

@a.app.route("/auth/google/callback")
def google_callback():
    state_received = a.request.args.get("state")
    state_stored = a.session.pop("oauth_state", None)  

    if state_received != state_stored:
        a.abort(400, "CSRF Warning! State mismatch.")  

    google = a.OAuth2Session(a.GOOGLE_CLIENT_ID, redirect_uri=a.REDIRECT_URI)
    token = google.fetch_token(a.GOOGLE_TOKEN_URL, client_secret=a.GOOGLE_CLIENT_SECRET,
                               authorization_response=a.request.url)

    user_info = google.get(a.GOOGLE_USER_INFO).json()
    return a.jsonify(user_info)  



@a.app.route('/check_token', methods=['GET'])
def check_token():
    
    token = a.request.headers.get('Authorization')
    if not token:
        return a.jsonify({"error": "Token missing!"}), 401
    try:
        # فك تشفير التوكن والتحقق من صحته
        decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
        a.user_id = decoded['user_id']  # يمكن استخدام user_id لاحقًا إذا لزم الأمر

        # إذا كان التوكن صالحًا، نعيد رسالة نجاح
        return a.jsonify({"message": "Token is valid!"}), 200

    except a.jwt.ExpiredSignatureError:
        return a.jsonify({"error": "Token has expired!"}), 401
    except a.jwt.InvalidTokenError:
        return a.jsonify({"error": "Invalid token!"}), 401
    except Exception as e:
        return a.jsonify({"error": f"An error occurred: {e}"}), 500
    
    

@a.app.route('/user_data', methods=['GET'])
def user_data():
    
    token = a.request.headers.get('Authorization')
    if not token:
        return a.jsonify({"error": "Token missing!"}), 401
    try:
        decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded['user_id']
        cursor = a.conn.cursor()

        
        query= 'select user_type from actor.user where user_id = %s'
        cursor.execute(query, (user_id,))
        user_type = cursor.fetchone()
        
        if user_type[0] == 'Owner':
            
                cursor.execute("""
                SELECT name, email, phone, user_name, company_name 
                FROM actor.user WHERE user_id = %s
                    """, (user_id,))
                user_data = cursor.fetchone()  # استرجاع صف واحد فقط

                # ✅ الاستعلام الثاني: جلب بيانات الباقة
                cursor.execute("""
                    SELECT p1, p2, p3, year, month, price 
                    FROM actor.package WHERE user_id = %s
                """, (user_id,))
                package_data = cursor.fetchall()  # استرجاع جميع الصفوف المتعلقة بالمستخدم

                cursor.close()

                # ✅ تجهيز البيانات للإرجاع
                user = { 
                    "name": user_data[0],
                    "email": user_data[1],
                    "phone": user_data[2],
                    "user_name": user_data[3],
                    "company_name": user_data[4],
                } if user_data else None

                packdge = [
                    {
                        "p1": row[0], "p2": row[1], "p3": row[2],
                        "year": row[3], "month": row[4], "price": row[5]
                    } for row in package_data
                ]

                return a.jsonify({"user": user, "packdge": packdge}), 200

        else:
          
            cursor.execute("SELECT name, email, phone , user_name , company_name FROM actor.user WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return a.jsonify({"name": user[0], "email": user[1], "phone": user[2] , "user_name" : user[3] , "company_name" : user[4]}), 200
        
    except Exception as e:
        return a.jsonify({"error": f"Invalid token: {e}"}), 401
