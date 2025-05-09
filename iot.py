import paho.mqtt.client as mqtt
import psycopg2
import json
from datetime import datetime
import time

# **الاتصال بقاعدة البيانات**
connection_string = "dbname=eden user=postgres password=ahmed2003 host=localhost port=5432"

def connect_db():
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print("❌ Database Connection Error:", e)
        return None, None

conn, cursor = connect_db()


def log_action_to_db(action_type):
    try:
        now = datetime.now()
        day, month, year = now.day, now.month, now.year
        current_time = now.strftime("%H:%M:%S")

        query = """
        INSERT INTO sensor_readings.actions (action_day, action_month, action_year, action_time, action_type)
        VALUES (%s, %s, %s, %s::TIME WITHOUT TIME ZONE, %s)
        """
        cursor.execute(query, (day, month, year, current_time, action_type))
        conn.commit()
        print(f"📝 Action Logged: Type={action_type}")

    except Exception as e:
        print("❌ Error logging action:", e)


# **جلب المرحلة الحالية والقيم min/max**
def get_current_stage_and_ranges():
    try:
        conn2, cursor2 = connect_db()
        if conn2 is None:
            return None, None

        cursor2.execute("SELECT DISTINCT day, month, year FROM sensor_readings.readings")
        dates = cursor2.fetchall()

        unique_dates = set()
        for day, month, year in dates:
            try:
                dt = datetime(year, month, day)
                unique_dates.add(dt)
            except:
                continue

        days_passed = len(unique_dates)
        print(f"📅 Unique days count: {days_passed}")

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

        current_stage = None
        for name, min_start, min_end, max_start, max_end in stages_timeline:
            if min_start <= days_passed <= min_end or max_start <= days_passed <= max_end:
                current_stage = name
                print(f"🌿 Current Stage: {current_stage}")
                break

        if current_stage is None:
            print("❌ Plant is outside the defined growth stages.")
            return None, None

        cursor2.execute("""
        SELECT temp_min, temp_max, humidity_min, humidity_max, intensity_min, intensity_max, salinity_min, salinity_max
        FROM tasmeed.tasmeed_iot
        WHERE stage = %s
        LIMIT 1
        """, (current_stage,))
        result = cursor2.fetchone()

        if result is None:
            print("❌ No min/max data found for this stage.")
            return current_stage, None

        thresholds = {
            'temp_min': result[0],
            'temp_max': result[1],
            'humidity_min': result[2],
            'humidity_max': result[3],
            'light_min': result[4],
            'light_max': result[5],
            'salt_min': result[6],
            'salt_max': result[7],
        }

        print("✅ Stage thresholds retrieved:", thresholds)
        return current_stage, thresholds

    except Exception as e:
        print("❌ Error:", e)
        return None, None

# **دالة استقبال الرسائل**
def on_message(client, userdata, msg):
    try:
        global conn, cursor

        if conn is None or conn.closed:
            print("🔄 Reconnecting to Database...")
            conn, cursor = connect_db()
            if conn is None:
                return

        payload = json.loads(msg.payload.decode())
        temperature = payload.get("temperature")
        humidity = payload.get("humidity")
        light = payload.get("light")
        salt = payload.get("salt")

        now = datetime.now()
        day, month, year = now.day, now.month, now.year
        current_time = now.strftime("%H:%M:%S")

        query = """
        INSERT INTO sensor_readings.readings (temperature, humidity, light, salt, day, month, year, time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::TIME WITHOUT TIME ZONE)
        """
        cursor.execute(query, (temperature, humidity, light, salt, day, month, year, current_time))
        conn.commit()
        print(f"✅ Data Inserted: Temp={temperature}, Humidity={humidity}, Light={light}, Salt={salt}")

        current_stage, thresholds = get_current_stage_and_ranges()
        if not thresholds:
            return

        temp_min = thresholds['temp_min']
        temp_max = thresholds['temp_max']
        humidity_min = thresholds['humidity_min']
        humidity_max = thresholds['humidity_max']
        intensity_min = thresholds['light_min']
        intensity_max = thresholds['light_max']
        salinity_min = thresholds['salt_min']
        salinity_max = thresholds['salt_max']

        if temperature is not None:
            if temperature < temp_min:
                diff = round(temp_min - temperature, 2)
                msg = f"⬇️ Temperature LOW: {temperature}°C (−{diff}°C below min {temp_min})"
                client.publish("esp32/alert", "1", qos=2)
                print(msg)
                log_action_to_db(msg)

            elif temperature > temp_max:
                diff = round(temperature - temp_max, 2)
                msg = f"⬆️ Temperature HIGH: {temperature}°C (+{diff}°C above max {temp_max})"
                client.publish("esp32/alert", "1", qos=2)
                print(msg)
                log_action_to_db(msg)

        if light is not None:
            if light < intensity_min:
                diff = round(intensity_min - light, 2)
                msg = f"⬇️ Light LOW: {light} lux (−{diff} below min {intensity_min})"
                client.publish("esp32/light", "2", qos=2)
                print(msg)
                log_action_to_db(msg)
            elif light > intensity_max:
                diff = round(light - intensity_max, 2)
                msg = f"⬆️ Light HIGH: {light} lux (+{diff} above max {intensity_max})"
                client.publish("esp32/light", "2", qos=2)
                print(msg)
                log_action_to_db(msg)

        if salt is not None:
            if salt < salinity_min:
                diff = round(salinity_min - salt, 2)
                msg = f"⬇️ Salinity LOW: {salt} (−{diff} below min {salinity_min})"
                client.publish("esp32/salt", "3", qos=2)
                print(msg)
                log_action_to_db(msg)
            elif salt > salinity_max:
                diff = round(salt - salinity_max, 2)
                msg = f"⬆️ Salinity HIGH: {salt} (+{diff} above max {salinity_max})"
                client.publish("esp32/salt", "3", qos=2)
                print(msg)
                log_action_to_db(msg)

        if humidity is not None:
            if humidity < humidity_min:
                diff = round(humidity_min - humidity, 2)
                msg = f"⬇️ Humidity LOW: {humidity}% (−{diff}% below min {humidity_min})"
                client.publish("esp32/humidity", "4", qos=2)
                print(msg)
                log_action_to_db(msg)
            elif humidity > humidity_max:
                diff = round(humidity - humidity_max, 2)
                msg = f"⬆️ Humidity HIGH: {humidity}% (+{diff}% above max {humidity_max})"
                client.publish("esp32/humidity", "4", qos=2)
                print(msg)
                log_action_to_db(msg)


    except Exception as e:
        print("❌ Error processing message:", e)

# **في حالة قطع الاتصال**
def on_disconnect(client, userdata, rc):
    print("⚠️ Disconnected from MQTT! Trying to reconnect...")
    while not client.is_connected():
        try:
            client.reconnect()
            print("✅ Reconnected!")
            break
        except Exception as e:
            print("❌ Reconnect failed:", e)
        time.sleep(5)

# **عند الاتصال بالبروكر**
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe("esp32/eden", qos=2)
    else:
        print(f"❌ Connection failed with code {rc}")

# **إعداد الـ MQTT Client**
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# **الاتصال بالبروكر**
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

client.loop_forever()