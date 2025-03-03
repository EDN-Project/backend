import app as a
import access
import sign_up


month = 0
code = 0
countries = []
country = 0
variety = 0


@a.app.route("/top_importers", methods=["POST"])
def top_importers():
    
    global month
    global code
    
    try:
        
        data = a.request.json
        plant_time = data.get("plant_time")
        code = data.get('code')
        
        if plant_time:
            month = a.datetime.fromisoformat(plant_time).month + 4  # حساب الشهر
        
        
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
                WHERE wd.month = {month}
                AND wd.year > (LatestYear.max_year - 5)
                AND wd.code = '{code}'
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
        
        countries = df['Importers'].unique().tolist()
        
        return a.jsonify({"top_importers": df.to_dict(orient="records") , "countries": countries})

        

    except Exception as e:
        print("❌ Error in /top_importers:", str(e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500


    

@a.app.route('/receive_country', methods=['POST'])
def receive_code_country():
    
    global country
    
    data = a.request.json  # استقبال البيانات كـ JSON
    country = data.get('country')

    
    if not country:
        return a.jsonify({'error': 'Missing code or country'}), 400
    
    return a.jsonify({'message': 'Data received', 'country': country})



@a.app.route('/recommended_month', methods=['POST'])
def recommended_month():
    
    try:
    
        cur = a.conn.cursor()
        
        # ✅ استعلام لحساب مجموع الكميات للمستورد المختار
        sum_query = f"""
            WITH LatestYear AS (
                SELECT MAX(year) AS max_year FROM global.world_demand
            )
            SELECT 
                SUM(CASE WHEN month = {month} THEN quantity ELSE 0 END) AS sum_current_month,
                SUM(CASE WHEN month = {month + 1} THEN quantity ELSE 0 END) AS sum_next_month,
                SUM(CASE WHEN month = {month + 2} THEN quantity ELSE 0 END) AS sum_after_next_month
            FROM global.world_demand
            WHERE importers = '{country}'
            AND year > (SELECT max_year - 5 FROM LatestYear)
            AND code = '{code}';
        """
        cur.execute(sum_query)
        sum_data = cur.fetchone()
        sum_current_month = sum_data[0] if sum_data[0] else 0
        sum_next_month = sum_data[1] if sum_data[1] else 0
        sum_after_next_month = sum_data[2] if sum_data[2] else 0

        cur.close()  # ✅ إغلاق الاتصال
        
        return a.jsonify({
            "sum_current_month": sum_current_month,
            "sum_next_month": sum_next_month,
            "sum_after_next_months": sum_after_next_month
        })

    except Exception as e:
        print("❌ Error in /recommended_month:", str(e))
        return a.jsonify({"error": str(e)}), 500



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
        
        cur.execute(query_data, (code, country))
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
        
        cur.execute(query_data, (code, country))
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
        
        cur.execute(query_data, (code, country))
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
        
        cur.execute(query_data, (code, country))
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
    
    


@a.app.route("/monafseen", methods=["GET"])
def monafseen():    
    
    try:
        cur = a.conn.cursor()
    
    
        cur.execute("""
        SELECT column_name
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name != 'code'
        ORDER BY ordinal_position DESC
        LIMIT 5
        """, ('world_supply',))  # اسم الجدول
        columns = [row[0] for row in cur.fetchall()]  # استخراج أسماء الأعمدة

        # توليد استعلام SQL ديناميكي باستخدام الأعمدة المستخرجة
        query = f"""
            SELECT exporters, {', '.join(columns)}
            FROM global.world_supply;
        """
        cur.execute(query)
        data = cur.fetchall()
        
        
        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            return a.jsonify(result)
        else:
            return a.jsonify({"error": "No data found for"}), 404
        
    
    except Exception as e:
        print("❌ Error in /monafseen:", str
              (e))  # خطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    


@a.app.route("/zo2_3am", methods=["GET"])
def zo2_3am():
    
    global variety
    
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
        
        cur.execute(query_data, (country,))  # ✅ تعديل تمرير المتغير
        data = cur.fetchone()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            variety = result.get("strawberry_variety")  # استخراج القيمة
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
    
    if not variety or not country:
        return a.jsonify({"error": "Please provide both 'variety' and 'country' as query parameters."}), 400

    if variety not in a.recommendations:
        return a.jsonify({"error": f"Variety '{variety}' not found. Please provide a valid variety."}), 404

    if country not in a.recommendations[variety]:
        return a.jsonify({"error": f"No recommendations found for variety '{variety}' in '{country}'."}), 404
    
    return a.jsonify({"variety": variety, "recommendation": a.recommendations[variety]})


if __name__ == '__main__':
    a.app.run(host='0.0.0.0', port=5000 , debug=True)
