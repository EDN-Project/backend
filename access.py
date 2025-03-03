import app as a


@a.app.route("/add_privilage_user", methods=["GET"])

def add_privilage_user():
    
    try:
        
        data = a.request.json
        company_id = data.get('country_id')
        email = data.get('email')
        give_access = data.get('give_access')
        global_access = data.get('global_access')
        data_sensor_access =data.get('data_sensor_acccess')
        daily_report = data.get('daily_report')
        ai_report = data.get('ai_report')
        user_type = data.get('user_type')
        
        
        token = a.request.headers.get('Authorization')
        decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded['user_id']  
        
        cur = a.conn.cursor()
    
        query =f'select company_id from actor.user where user_id ={user_id}'
        
        cur.execute(query)
        stored_password = cur.fetchone()  # جلب كل البيانات
        if isinstance(stored_password, bytes):
            stored_password = stored_password.decode('utf-8')
        
        # ✅ التحقق من كلمة المرور
        if a.bcrypt.checkpw(company_id.encode('utf-8'), stored_password.encode('utf-8')):
           query = """UPDATE actor.user
           SET give_access = %s,
               global_access = %s,
               data_sensor_access = %s,
               daily_report = %s,
               ai_report = %s,
               user_type = %s,
               company_id = %s
           WHERE email = %s;"""

           cur.execute(query, (give_access, global_access, data_sensor_access, daily_report, ai_report, user_type, company_id , email))
           a.conn.commit()
           cur.close()  

            
           return a.jsonify({"message": "Added successfully!"}), 200
        else:
            return a.jsonify({"error": "Invalid password!"}), 401
       
    except Exception as e:
        print("❌ Error in /add_privilage_user:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500


@a.app.route("/give_access", methods=["GET"])
def give_access():
    
    try:
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
        
            with a.conn.cursor() as cur:
                
                decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
                user_id = decoded['user_id']
                
                query = "SELECT give_access FROM actor.user WHERE user_id = %s;"
                cur.execute(query, (user_id,))
                data = cur.fetchone()
            
            if data and data[0] == 1:
                return a.jsonify({"message": "You have access!", "access": True}), 200
            else:
                return a.jsonify({"message": "You don't have access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500

@a.app.route("/global_access", methods=["GET"])
def global_access():
    try:
        
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
        
            with a.conn.cursor() as cur:
                query = "SELECT global_access FROM actor.user WHERE user_id = %s;"
                cur.execute(query, (user_id,))
                data = cur.fetchone()
            
            if data and data[0] == 1:
                return a.jsonify({"message": "You have global access!", "access": True}), 200
            else:
                return a.jsonify({"message": "You don't have global access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500
    


@a.app.route("/data_sensor_access", methods=["GET"])
def data_sensor_access():
    
    try:
        
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
        
            with a.conn.cursor() as cur:
                query = "SELECT data_sensor_access FROM actor.user WHERE user_id = %s;"
                cur.execute(query, (user_id,))
                data = cur.fetchone()
            
            if data and data[0] == 1:
                return a.jsonify({"message": "You have data sensor access!", "access": True , "user_id":user_id}), 200
            else:
                return a.jsonify({"message": "You don't have  data sensor access!", "access": False , "user_id":user_id}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500


@a.app.route("/daily_report", methods=["GET"])
def daily_report():
    try:
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
        
            with a.conn.cursor() as cur:
                query = "SELECT daily_report FROM actor.user WHERE user_id = %s;"
                cur.execute(query, (user_id,))
                data = cur.fetchone()
            
            if data and data[0] == 1:
                return a.jsonify({"message": "You have daily report access!", "access": True}), 200
            else:
                return a.jsonify({"message": "You don't have  daily report access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500


@a.app.route("/ai_report", methods=["GET"])
def ai_report():
    try:
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
        
            with a.conn.cursor() as cur:
                query = "SELECT ai_report FROM actor.user WHERE user_id = %s;"
                cur.execute(query, (user_id,))
                data = cur.fetchone()
            
            if data and data[0] == 1:
                return a.jsonify({"message": "You have ai report access!", "access": True}), 200
            else:
                return a.jsonify({"message": "You don't have  ai report access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500  
