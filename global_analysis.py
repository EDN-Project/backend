import app as a
import access
import sign_up


@a.app.route("/submit_time", methods=["POST"])
def submit_time():

    data = a.request.json
    plant_time = data.get("plant_time")

    if not plant_time:
        return a.jsonify({"error": "Plant time is required"}), 400

    a.month = a.datetime.fromisoformat(plant_time).month + 4  # حساب الشهر

    return a.jsonify({"message": f"Received month: {a.month}"})


@a.app.route("/top_importers_frozen", methods=["GET"])
def top_importers_frozen():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query = f"""
                        WITH LatestYear AS (
                SELECT MAX(year) AS max_year FROM global.world_demand
            ),
            RankedData AS (
                SELECT 
                    wd.importers, 
                    wd.year, 
                    wd.month, 
                    wd.quantity,
                    RANK() OVER (PARTITION BY wd.year ORDER BY wd.quantity DESC) AS rank
                FROM global.world_demand wd
                CROSS JOIN LatestYear
                WHERE wd.month = {a.month}
                AND wd.year > (LatestYear.max_year - 5)
                AND wd.code = '081110'
            )
            SELECT importers, year, month, quantity
            FROM RankedData
            WHERE rank <= 5 
            ORDER BY year DESC, quantity DESC;
        """

        # ✅ تنفيذ الاستعلام وجلب البيانات
        cur.execute(query)
        data = cur.fetchall()  # جلب كل البيانات

        # ✅ تحويل البيانات إلى DataFrame
        df = a.pd.DataFrame(data, columns=["Importers", "year", "month", "quantity"])
        
        a.countries = df['Importers'].unique().tolist()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        return a.jsonify({"top_importers": df.to_dict(orient="records")})

    except Exception as e:
        print("❌ Error in /top_importers:", str(e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500


@a.app.route("/top_importers_fresh", methods=["GET"])
def top_importers_fresh():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query = f"""
                        WITH LatestYear AS (
                SELECT MAX(year) AS max_year FROM global.world_demand
            ),
            RankedData AS (
                SELECT 
                    wd.importers, 
                    wd.year, 
                    wd.month, 
                    wd.quantity,
                    RANK() OVER (PARTITION BY wd.year ORDER BY wd.quantity DESC) AS rank
                FROM global.world_demand wd
                CROSS JOIN LatestYear
                WHERE wd.month = {a.month}
                AND wd.year > (LatestYear.max_year - 5)
                AND wd.code = '081010'
            )
            SELECT importers, year, month, quantity
            FROM RankedData
            WHERE rank <= 5 
            ORDER BY year DESC, quantity DESC;
        """

        # ✅ تنفيذ الاستعلام وجلب البيانات
        cur.execute(query)
        data = cur.fetchall()  # جلب كل البيانات

        # ✅ تحويل البيانات إلى DataFrame
        df = a.pd.DataFrame(data, columns=["Importers", "year", "month", "quantity"])
        
        a.countries = df['Importers'].unique().tolist()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        return a.jsonify({"top_importers": df.to_dict(orient="records")})

    except Exception as e:
        print("❌ Error in /top_importers:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500



@a.app.route("/get_countries", methods=["GET"])
def get_countries():
    try:
        return a.jsonify({"countries": a.countries})  # إرسالها كـ JSON
    except Exception as e:
        return a.jsonify({"error": str(e)}), 500  # في حالة حدوث خطأ

    
    

@a.app.route('/receive_code_country', methods=['POST'])
def receive_code_country():
    
    data = a.request.json  # استقبال البيانات كـ JSON
    a.code = data.get('code')
    a.country = data.get('country')
    
    if not a.code or not a.country:
        return a.jsonify({'error': 'Missing code or country'}), 400
    
    return a.jsonify({'message': 'Data received', 'code': a.code, 'country': a.country})



@a.app.route("/country_price", methods=["GET"])
def country_price():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('values_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        # تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM global.values_egypt
            WHERE code = %s AND importers = %s
        """
        
        cur.execute(query_data, (a.code, a.country))
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given code and country"}), 404

    except Exception as e:
        print("❌ Error in /country_price:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    
    


@a.app.route("/country_quantity", methods=["GET"])
def country_quantity():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('quantity_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        # تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM global.quantity_egypt
            WHERE code = %s AND importers = %s
        """
        
        cur.execute(query_data, (a.code, a.country))
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given code and country"}), 404

    except Exception as e:
        print("❌ Error in /country_quantity:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    
    
    
    
@a.app.route("/country_growth_value", methods=["GET"])
def country_growth_value():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('growth_value_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        # تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM global.growth_value_egypt
            WHERE code = %s AND importers = %s
        """
        
        cur.execute(query_data, (a.code, a.country))
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given code and country"}), 404

    except Exception as e:
        print("❌ Error in /country_growth_value:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    
    
    

@a.app.route("/country_growth_quantity", methods=["GET"])
def country_growth_qunatity():
    
    try:
        cur = a.conn.cursor()

        # ✅ تعديل الاستعلام وإضافة اسم الجدول
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('growth_quantity_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        # تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM global.growth_quantity_egypt
            WHERE code = %s AND importers = %s
        """
        
        cur.execute(query_data, (a.code, a.country))
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given code and country"}), 404

    except Exception as e:
        print("❌ Error in /country_growth_quantity:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    
    


@a.app.route("/zo2_3am", methods=["GET"])
def zo2_3am():
    
    try:
        cur = a.conn.cursor()

        # ✅ جلب أسماء الأعمدة
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position DESC
        """
        cur.execute(query_columns, ('elzo2_el3am',))
        columns = [col[0] for col in cur.fetchall()]

        # ✅ تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM tasmeed.elzo2_el3am
            WHERE country = %s
        """
        
        cur.execute(query_data, (a.country,))  # ✅ تعديل تمرير المتغير
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            a.variety = result.get("strawberry_variety")  # استخراج القيمة
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given country"}), 404

    except Exception as e:
        print("❌ Error in /zo2_3am:", str(e))  # طباعة الخطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    



@a.app.route("/tasmeed", methods=["GET"])
def tasmeed():
    try:
        cur = a.conn.cursor()

        # ✅ جلب أسماء الأعمدة
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position DESC
        """
        cur.execute(query_columns, ('tasmeed',))
        columns = [col[0] for col in cur.fetchall()]

        # ✅ تكوين استعلام ديناميكي لاختيار البيانات من الأعمدة المحددة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM tasmeed.tasmeed
        """
        
        cur.execute(query_data)  # ✅ تعديل تمرير المتغير
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for the given country"}), 404

    except Exception as e:
        print("❌ Error in /tasmeed:", str(e))  # طباعة الخطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    

@a.app.route('/recommend_tasmeed', methods=['GET'])
def recommend():
    
    if a.variety not in a.recommendations:
        return a.jsonify({"error": "Variety not found. Please provide a valid variety."}), 404
    
    return a.jsonify({"variety": a.variety, "recommendation": a.recommendations[a.variety]})


if __name__ == '__main__':
    a.app.run(host='0.0.0.0', port=5000 , debug=True)