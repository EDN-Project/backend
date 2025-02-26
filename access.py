import app as a


@a.app.route("/give_access", methods=["GET"])
def give_access():
    try:
        with a.conn.cursor() as cur:
            query = "SELECT give_access FROM actor.user WHERE user_id = %s;"
            cur.execute(query, (a.user_id,))
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
        with a.conn.cursor() as cur:
            query = "SELECT global_access FROM actor.user WHERE user_id = %s;"
            cur.execute(query, (a.user_id,))
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
        with a.conn.cursor() as cur:
            query = "SELECT data_sensor_access FROM actor.user WHERE user_id = %s;"
            cur.execute(query, (a.user_id,))
            data = cur.fetchone()
        
        if data and data[0] == 1:
            return a.jsonify({"message": "You have data sensor access!", "access": True}), 200
        else:
            return a.jsonify({"message": "You don't have  data sensor access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500


@a.app.route("/daily_report", methods=["GET"])
def daily_report():
    try:
        with a.conn.cursor() as cur:
            query = "SELECT daily_report FROM actor.user WHERE user_id = %s;"
            cur.execute(query, (a.user_id,))
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
        with a.conn.cursor() as cur:
            query = "SELECT ai_report FROM actor.user WHERE user_id = %s;"
            cur.execute(query, (a.user_id,))
            data = cur.fetchone()
        
        if data and data[0] == 1:
            return a.jsonify({"message": "You have ai report access!", "access": True}), 200
        else:
            return a.jsonify({"message": "You don't have  ai report access!", "access": False}), 200

    except Exception as e:
        return a.jsonify({"error": str(e)}), 500  