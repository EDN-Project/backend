import paho.mqtt.client as mqtt
import psycopg2
import json
from datetime import datetime
import time
import random

# Database Connection
connection_string = "dbname=eden user=postgres password=ahmed2003 host=db port=5432"

def connect_db():
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print("❌ Database Connection Error:", e)
        return None, None

conn, cursor = connect_db()


def log_action_to_db(cursor, action_type):
    try:
        now = datetime.now()
        day, month, year = now.day, now.month, now.year
        current_time = str(now.hour)  # تخزين رقم الساعة فقط

        query = """
        INSERT INTO sensor_readings.actions (action_day, action_month, action_year, action_time, action_type)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (day, month, year, current_time, action_type))
        print(f"📝 Action Logged: Type={action_type}")

    except Exception as e:
        print("❌ Error logging action:", e)
        raise


# Get current stage and min/max values
def get_current_stage_and_ranges(cursor):
    try:
        cursor.execute("SELECT DISTINCT day, month, year FROM sensor_readings.readings")
        dates = cursor.fetchall()

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

        cursor.execute("""
        SELECT temp_min, temp_max, humidity_min, humidity_max, intensity_min, intensity_max, salinity_min, salinity_max
        FROM tasmeed.tasmeed_iot
        WHERE stage = %s
        LIMIT 1
        """, (current_stage,))
        result = cursor.fetchone()

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

# Message receiving function
def on_message(client, userdata, msg):
    try:
        # تجاهل الرسائل القديمة (retained)
        if msg.retain:
            print("🛑 Ignored retained message")
            return

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
        current_time = str(now.hour)  # تخزين رقم الساعة فقط

        try:
            # Start a transaction
            conn.autocommit = False
            
            # Lock the tables to prevent concurrent inserts
            cursor.execute("LOCK TABLE sensor_readings.readings IN EXCLUSIVE MODE")
            
            # Check if reading already exists for this timestamp
            cursor.execute("""
                SELECT COUNT(*) FROM sensor_readings.readings 
                WHERE day = %s AND month = %s AND year = %s AND time = %s
            """, (day, month, year, current_time))
            
            if cursor.fetchone()[0] > 0:
                print("⚠️ Reading already exists for this timestamp, skipping...")
                conn.rollback()
                return
            
            # Get current stage and thresholds once
            current_stage, thresholds = get_current_stage_and_ranges(cursor)
            
            # Set default pH and EC values
            ph = 6.0  # Default values
            ec = 1.5

            if current_stage:
                # Get optimal ph and ec values based on current stage
                cursor.execute("""
                    SELECT ph_min, ph_max, ec_min, ec_max
                    FROM tasmeed.tasmeed_iot
                    WHERE stage = %s
                    LIMIT 1
                """, (current_stage,))
                ranges = cursor.fetchone()
                if ranges:
                    # Calculate random optimal values within the allowed range
                    ph_min, ph_max = ranges[0], ranges[1]
                    ec_min, ec_max = ranges[2], ranges[3]
                    
                    # Generate random values within 20% of the middle range
                    ph_mid = (ph_max + ph_min) / 2
                    ph_range = (ph_max - ph_min) * 0.2  # 20% of total range
                    ph = round(random.uniform(ph_mid - ph_range, ph_mid + ph_range), 2)
                    
                    ec_mid = (ec_max + ec_min) / 2
                    ec_range = (ec_max - ec_min) * 0.2  # 20% of total range
                    ec = round(random.uniform(ec_mid - ec_range, ec_mid + ec_range), 2)
                    
                    # Ensure values stay within min-max bounds
                    ph = max(ph_min, min(ph_max, ph))
                    ec = max(ec_min, min(ec_max, ec))

            # Insert sensor readings with ph and ec
            query = """
            INSERT INTO sensor_readings.readings (temperature, humidity, light, salt, ph, ec, day, month, year, time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (temperature, humidity, light, salt, ph, ec, day, month, year, current_time))

            alerts = []  # Store alerts to be logged

            if temperature is not None:
                if temperature < thresholds['temp_min']:
                    diff = round(thresholds['temp_min'] - temperature, 2)
                    msg = f"⬇️ Temperature LOW: {temperature}°C (−{diff}°C below min {thresholds['temp_min']})"
                    client.publish("esp32/alert", "1", qos=1)
                    print(msg)
                    alerts.append(msg)

                elif temperature > thresholds['temp_max']:
                    diff = round(temperature - thresholds['temp_max'], 2)
                    msg = f"⬆️ Temperature HIGH: {temperature}°C (+{diff}°C above max {thresholds['temp_max']})"
                    client.publish("esp32/alert", "1", qos=1)
                    print(msg)
                    alerts.append(msg)

            if light is not None:
                if light < thresholds['light_min']:
                    diff = round(thresholds['light_min'] - light, 2)
                    msg = f"⬇️ Light LOW: {light} lux (−{diff} below min {thresholds['light_min']})"
                    client.publish("esp32/light", "2", qos=1)
                    print(msg)
                    alerts.append(msg)
                elif light > thresholds['light_max']:
                    diff = round(light - thresholds['light_max'], 2)
                    msg = f"⬆️ Light HIGH: {light} lux (+{diff} above max {thresholds['light_max']})"
                    client.publish("esp32/light", "2", qos=1)
                    print(msg)
                    alerts.append(msg)

            if salt is not None:
                if salt < thresholds['salt_min']:
                    diff = round(thresholds['salt_min'] - salt, 2)
                    msg = f"⬇️ Salinity LOW: {salt} (−{diff} below min {thresholds['salt_min']})"
                    client.publish("esp32/salt", "3", qos=1)
                    print(msg)
                    alerts.append(msg)
                elif salt > thresholds['salt_max']:
                    diff = round(salt - thresholds['salt_max'], 2)
                    msg = f"⬆️ Salinity HIGH: {salt} (+{diff} above max {thresholds['salt_max']})"
                    client.publish("esp32/salt", "3", qos=1)
                    print(msg)
                    alerts.append(msg)

            if humidity is not None:
                if humidity < thresholds['humidity_min']:
                    diff = round(thresholds['humidity_min'] - humidity, 2)
                    msg = f"⬇️ Humidity LOW: {humidity}% (−{diff}% below min {thresholds['humidity_min']})"
                    client.publish("esp32/humidity", "4", qos=1)
                    print(msg)
                    alerts.append(msg)
                elif humidity > thresholds['humidity_max']:
                    diff = round(humidity - thresholds['humidity_max'], 2)
                    msg = f"⬆️ Humidity HIGH: {humidity}% (+{diff}% above max {thresholds['humidity_max']})"
                    client.publish("esp32/humidity", "4", qos=1)
                    print(msg)
                    alerts.append(msg)

            # Log all alerts in the same transaction
            for alert in alerts:
                log_action_to_db(cursor, alert)

            # Commit everything at once
            conn.commit()
            print(f"✅ Data Inserted: Temp={temperature}, Humidity={humidity}, Light={light}, Salt={salt}, pH={ph}, EC={ec}")
            
        except Exception as e:
            # If there's an error, rollback the transaction
            conn.rollback()
            print("❌ Error in database transaction:", e)
            return
        finally:
            # Reset autocommit
            conn.autocommit = True

    except Exception as e:
        print("❌ Error processing message:", e)

# On disconnection
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

# On broker connection
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe("esp32/eden", qos=2)
    else:
        print(f"❌ Connection failed with code {rc}")

def setup_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect("broker.hivemq.com", 1883, 60)
        print("✅ Successfully connected to HiveMQ MQTT Broker!")
    except Exception as e:
        print("❌ Failed to connect to MQTT Broker:", e)
    
    return client

if __name__ == "__main__":
    # This code will only run when the file is executed directly
    client = setup_mqtt_client()
    client.loop_forever()