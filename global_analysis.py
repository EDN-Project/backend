import app as a
import access
import sign_up
import payment
import iot_back
import ai
import threading
from iot import setup_mqtt_client

# تهيئة IoT thread
def start_iot_service():
    try:
        print("🚀 Starting IoT Service...")
        client = setup_mqtt_client()
        client.loop_forever()
    except Exception as e:
        print("❌ IoT Service Error:", e)

# بدء تشغيل IoT thread
iot_thread = threading.Thread(target=start_iot_service, daemon=True)
iot_thread.start()

@a.app.route("/top_importers", methods=["POST"])
def top_importers():
    try:
        data = a.request.json
        plant_time = data.get("plant_time")
        code = data.get("code")

        # حساب الشهر بناءً على plant_time
        month = a.datetime.fromisoformat(plant_time).month + 4 if plant_time else None

        cur = a.conn.cursor()

        query = """
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
                WHERE wd.month = %s
                AND wd.year > (LatestYear.max_year - 5)
                AND wd.code = %s
            )
            SELECT importers, year, month, quantity
            FROM RankedData
            WHERE rank <= 5 
            ORDER BY year DESC, quantity DESC;
        """

        cur.execute(query, (month, code))
        data = cur.fetchall()
        cur.close()  # ✅ إغلاق الـ cursor بعد الاستخدام

        # ✅ استخراج قائمة الدول
        countries = list(set(row[0] for row in data))

        # ✅ تحويل البيانات إلى الشكل المطلوب
        from collections import defaultdict
        result = defaultdict(dict)

        for importer, year, month, quantity in data:
            result[year]["year"] = year
            result[year][importer] = quantity

        response_data = list(result.values())

        return a.jsonify({"top_importers": response_data, "countries": countries , "code" : code , "month" : month})

    except Exception as e:
        print("❌ Error in /top_importers:", str(e))
        return a.jsonify({"error": str(e)}), 500

    

@a.app.route('/receive_country', methods=['POST'])
def receive_code_country():
    data = a.request.json  # استقبال البيانات كـ JSON
    country = data.get('country')

    if not country :
        return a.jsonify({'error': 'Missing code or country'}), 400
    
    return a.jsonify({'message': 'Data received', 'country': country})



@a.app.route('/recommended_month', methods=['POST'])
def recommended_month():
    try:
        data = a.request.json  # استقبال البيانات كـ JSON
        month = data.get("month")
        country = data.get("country")
        code = data.get("code")

        # ✅ التحقق من القيم المدخلة
        if month is None or not country or not code:
            return a.jsonify({"error": "Missing required parameters"}), 400

        cur = a.conn.cursor()
        
        # ✅ استعلام لحساب مجموع الكميات للمستورد المختار
        sum_query = """
            WITH LatestYear AS (
                SELECT MAX(year) AS max_year FROM global.world_demand
            )
            SELECT 
                SUM(CASE WHEN month = %s THEN quantity ELSE 0 END) AS sum_current_month,
                SUM(CASE WHEN month = %s THEN quantity ELSE 0 END) AS sum_next_month,
                SUM(CASE WHEN month = %s THEN quantity ELSE 0 END) AS sum_after_next_month
            FROM global.world_demand
            WHERE importers = %s
            AND year > (SELECT max_year - 5 FROM LatestYear)
            AND code = %s;
        """
        
        cur.execute(sum_query, (month, month + 1, month + 2, country, code))
        sum_data = cur.fetchone()
        cur.close()  # ✅ إغلاق الاتصال بعد الاستخدام
        
        # ✅ تعيين القيم الافتراضية إذا كانت None
        sum_current_month = sum_data[0] or 0
        sum_next_month = sum_data[1] or 0
        sum_after_next_month = sum_data[2] or 0

        return a.jsonify({
            "sum_current_month": sum_current_month,
            "sum_next_month": sum_next_month,
            "sum_after_next_months": sum_after_next_month
        })

    except Exception as e:
        print("❌ Error in /recommended_month:", str(e))
        return a.jsonify({"error": str(e)}), 500



@a.app.route("/country_price", methods=["POST"])
def country_price():
    try:
        data = a.request.json  # استقبال البيانات كـ JSON
        code = data.get("code")
        country = data.get("country")

        # ✅ التحقق من القيم المدخلة
        if not code or not country:
            return a.jsonify({"error": "Missing required parameters"}), 400

        cur = a.conn.cursor()

        # ✅ جلب آخر 10 أعمدة (باستثناء code)
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('values_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        if not columns:
            return a.jsonify({"error": "No columns found"}), 500

        # ✅ تكوين استعلام ديناميكي باستخدام placeholders
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
        print("❌ Error in /country_price:", str(e))
        return a.jsonify({"error": str(e)}), 500
    
    


@a.app.route("/country_quantity", methods=["POST"])
def country_quantity():
    try:
        data = a.request.json  # استقبال البيانات كـ JSON
        code = data.get("code")
        country = data.get("country")

        # ✅ التحقق من القيم المدخلة
        if not code or not country:
            return a.jsonify({"error": "Missing required parameters"}), 400

        cur = a.conn.cursor()

        # ✅ جلب آخر 10 أعمدة من الجدول (باستثناء code)
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('quantity_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        if not columns:
            return a.jsonify({"error": "No columns found"}), 500

        # ✅ تكوين استعلام ديناميكي بطريقة آمنة
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
        print("❌ Error in /country_quantity:", str(e))
        return a.jsonify({"error": str(e)}), 500
    
    
    
    
@a.app.route("/country_growth_value", methods=["POST"])
def country_growth_value():
    try:
        data = a.request.json  # استقبال البيانات كـ JSON
        code = data.get("code")
        country = data.get("country")

        # ✅ التحقق من القيم المدخلة
        if not code or not country:
            return a.jsonify({"error": "Missing required parameters"}), 400

        cur = a.conn.cursor()

        # ✅ جلب آخر 10 أعمدة من الجدول (باستثناء code)
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('growth_value_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        if not columns:
            return a.jsonify({"error": "No columns found"}), 500

        # ✅ تكوين استعلام ديناميكي بطريقة آمنة
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
        print("❌ Error in /country_growth_value:", str(e))
        return a.jsonify({"error": str(e)}), 500
    
    
    

@a.app.route("/country_growth_quantity", methods=["POST"])
def country_growth_quantity():
    try:
        data = a.request.json  # 📥 استقبال البيانات كـ JSON
        code = data.get("code")
        country = data.get("country")

        # ✅ التحقق من القيم المدخلة
        if not code or not country:
            return a.jsonify({"error": "Missing required parameters"}), 400

        cur = a.conn.cursor()

        # ✅ جلب آخر 10 أعمدة من الجدول (باستثناء code)
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name != 'code'
            ORDER BY ordinal_position DESC
            LIMIT 10
        """
        cur.execute(query_columns, ('growth_quantity_egypt',))
        columns = [col[0] for col in cur.fetchall()]

        if not columns:
            return a.jsonify({"error": "No columns found"}), 500

        # ✅ تكوين استعلام ديناميكي بطريقة آمنة
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
        print("❌ Error in /country_growth_quantity:", str(e))
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
    


@a.app.route("/zo2_3am", methods=["POST"])
def zo2_3am():
    try:
        data = a.request.json  # 📥 استقبال البيانات كـ JSON
        country = data.get("country")

        # ✅ التحقق من إدخال قيمة البلد
        if not country:
            return a.jsonify({"error": "Missing required parameter: country"}), 400

        cur = a.conn.cursor()

        # ✅ جلب أسماء الأعمدة من الجدول
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position DESC
        """
        cur.execute(query_columns, ('elzo2_el3am',))
        columns = [col[0] for col in cur.fetchall()]

        if not columns:
            return a.jsonify({"error": "No columns found"}), 500

        # ✅ تكوين استعلام ديناميكي بطريقة آمنة
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM tasmeed.elzo2_el3am
            WHERE country = %s
        """
        
        cur.execute(query_data, (country,))
        data = cur.fetchone()
        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            result = dict(zip(columns, data))
            variety = result.get("strawberry_variety")  # استخراج قيمة
            return a.jsonify({"result": result, "variety": variety})
        else:
            return a.jsonify({"error": "No data found for the given country"}), 404

    except Exception as e:
        print("❌ Error in /zo2_3am:", str(e))  # طباعة الخطأ في التيرمينال
        return a.jsonify({"error": str(e)}), 500
    



@a.app.route("/tasmeed", methods=["GET"])

def determine_plant_stage(days_passed):
    raw_stages = [
        ("Seed Germination and Early Seedling", 7, 17),
        ("Vegetative Growth", 30, 50),
        ("Flowering", 20, 30),
        ("Fruiting", 30, 45),
        ("Harvesting", 10, 20),
        ("Post-Harvest", 10, 20),
    ]

    stages_timeline = []
    start_min = 0
    start_max = 0

    for name, min_duration, max_duration in raw_stages:
        end_min = start_min + min_duration
        end_max = start_max + max_duration
        stages_timeline.append((name, start_min, end_min, start_max, end_max))
        start_min = end_min
        start_max = end_max

    for name, min_start, min_end, max_start, max_end in stages_timeline:
        if min_start <= days_passed <= min_end or max_start <= days_passed <= max_end:
            return name

    return None


def tasmeed():
    try:
        cur = a.conn.cursor()

        # ✅ الحصول على جميع التواريخ من قاعدة البيانات
        cur.execute("SELECT DISTINCT day, month, year FROM sensor_readings.readings")
        dates = cur.fetchall()

        unique_dates = set()
        for day, month, year in dates:
            try:
                dt = a.datetime(year, month, day)
                unique_dates.add(dt)
            except:
                continue

        days_passed = len(unique_dates)
        print(f"📅 Days passed: {days_passed}")

        # ✅ تحديد المرحلة الحالية بناءً على عدد الأيام
        current_stage = determine_plant_stage(days_passed)
        print(f"🌱 Current Stage: {current_stage}")

        if not current_stage:
            return a.jsonify({"error": "Could not determine current stage"}), 404

        # ✅ جلب أسماء الأعمدة
        query_columns = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position DESC
        """
        cur.execute(query_columns, ('tasmeed',))
        columns = [col[0] for col in cur.fetchall()]

        # ✅ جلب البيانات الخاصة بالمرحلة الحالية
        query_data = f"""
            SELECT {', '.join([f'"{col}"' for col in columns])}
            FROM tasmeed.tasmeed 
            WHERE stage = %s
        """
        cur.execute(query_data, (current_stage,))
        data = cur.fetchall()

        cur.close()  # ✅ إغلاق الاتصال بعد الانتهاء

        if data:
            # ✅ نفس الشكل القديم للبيانات مع إضافة المفتاح الجديد "stage"
            result = [dict(zip(columns, row)) for row in data]
            return a.jsonify({
                "stage": current_stage,
                "data": result
            })
        else:
            return a.jsonify({
                "stage": current_stage,
                "data": []
            }), 404

    except Exception as e:
        print("❌ Error in /tasmeed:", str(e))
        return a.jsonify({"error": str(e)}), 500
    
    


@a.app.route('/recommend_tasmeed', methods=['POST'])
def recommend():
    
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
    
    data = a.request.json  # 📥 استقبال البيانات كـ JSON
    
    variety = data.get("variety")
    country = data.get("country")

    # ✅ التحقق من أن كلا المتغيرين متوفران
    if not variety or not country:
        return a.jsonify({"error": "Please provide both 'variety' and 'country' as query parameters."}), 400

    # ✅ التحقق من أن `variety` موجود في القاموس
    if variety not in recommendations:
        return a.jsonify({"error": f"Variety '{variety}' not found. Please provide a valid variety."}), 404

    # ✅ التحقق من أن `country` موجود في `variety`
    if country not in recommendations[variety]:
        return a.jsonify({"error": f"No recommendations found for variety '{variety}' in '{country}'."}), 404
    
    return a.jsonify({"variety": variety, "country": country, "recommendation": recommendations[variety][country]})



if __name__ == '__main__':
    a.app.run(host='0.0.0.0', port=5000 , debug=True)