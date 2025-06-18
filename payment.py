import app as a

@a.app.route("/password_farm", methods=["POST"])
def password_farm():
    
    
    try:
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            
            cur = a.conn.cursor()
            
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
    
            data = a.request.get_json()
            
            company_id = data.get("company_id")
            
            hashed_company_id = a.hash_password(company_id)
            
            query = """UPDATE actor.user
            SET
            company_id = %s
            WHERE user_id = %s;"""
            
            cur.execute(query, (hashed_company_id , user_id))
            a.conn.commit()
            cur.close() 
            
            return a.jsonify({"message": "Company ID added succesfully!"}), 401 
    
    except Exception as e:
        return a.jsonify({"error": str(e)}), 500    



@a.app.route("/update_user_package", methods=["POST"])
def update_user_package():
    try:
        
        token = a.request.headers.get('Authorization')
        if not token:
            return a.jsonify({"error": "Token missing!"}), 401
        
        else:
            
            decoded = a.jwt.decode(token, a.app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = decoded['user_id']
    
            data = a.request.get_json()

            package = data.get("package") # p1, p2, p3
            price = data.get("price")

            if not user_id or package not in ["p1", "p2", "p3"]:
                return a.jsonify({"error": "Invalid input"}), 400

            now = a.datetime.now()
            month = now.month
            year = now.year

            with a.conn.cursor() as cur:
            
                update_user_query = "UPDATE actor.user SET user_type = 'Owner' WHERE user_id = %s;"
                cur.execute(update_user_query, (user_id,))

                insert_package_query = """
                INSERT INTO actor.package (user_id, p1, p2, p3, month, year, price) 
                VALUES (%s, 
                CASE WHEN %s = 'p1' THEN TRUE ELSE FALSE END, 
                CASE WHEN %s = 'p2' THEN TRUE ELSE FALSE END, 
                CASE WHEN %s = 'p3' THEN TRUE ELSE FALSE END, 
                %s, %s, %s
                        );
                """

                cur.execute(insert_package_query, (user_id, package, package, package, month, year, price))

                a.conn.commit()

            return a.jsonify({"message": "User upgraded to Owner and package subscribed successfully!"}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500