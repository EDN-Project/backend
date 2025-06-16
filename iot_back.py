import app as a

def determine_plant_stage(days_passed):
    # Define the growth stages with their durations
    raw_stages = [
        ("Seed Germination and Early Seedling", 7, 17),
        ("Vegetative Growth", 30, 50),
        ("Flowering", 20, 30),
        ("Fruiting", 30, 45),
        ("Harvesting", 10, 20),
        ("Post-Harvest", 10, 20),
    ]
    
    # Calculate the timeline for each stage
    stages_timeline = []
    start_min = 0
    start_max = 0
    
    for name, min_duration, max_duration in raw_stages:
        end_min = start_min + min_duration
        end_max = start_max + max_duration
        stages_timeline.append((name, start_min, end_min, start_max, end_max))
        start_min = end_min
        start_max = end_max
    
    # Determine current stage based on days passed
    for name, min_start, min_end, max_start, max_end in stages_timeline:
        if min_start <= days_passed <= min_end or max_start <= days_passed <= max_end:
            return name
            
    return None

def format_readings(readings, columns):
    formatted_data = []
    for row in readings:
        reading_dict = dict(zip(columns, row))
        # Convert time to string format if it's a datetime object
        if isinstance(reading_dict['time'], a.datetime):
            reading_dict['time'] = reading_dict['time'].strftime('%H:%M:%S')
        formatted_data.append(reading_dict)
    
    return {
        'status': 'success',
        'count': len(formatted_data),
        'data': formatted_data
    }

def calculate_daily_averages(readings):
    daily_readings = {}
    
    # تجميع القراءات حسب اليوم
    for reading in readings:
        day_key = (reading[0], reading[1], reading[2])  # day, month, year
        if day_key not in daily_readings:
            daily_readings[day_key] = {
                'day': reading[0],
                'month': reading[1],
                'year': reading[2],
                'readings_count': 0,
                'ph_sum': 0,
                'temperature_sum': 0,
                'humidity_sum': 0,
                'salt_sum': 0,
                'light_sum': 0,
                'ec_sum': 0
            }
        
        daily_readings[day_key]['readings_count'] += 1
        daily_readings[day_key]['ph_sum'] += reading[4]  # ph
        daily_readings[day_key]['temperature_sum'] += reading[5]  # temperature
        daily_readings[day_key]['humidity_sum'] += reading[6]  # humidity
        daily_readings[day_key]['salt_sum'] += reading[7]  # salt
        daily_readings[day_key]['light_sum'] += reading[8]  # light
        daily_readings[day_key]['ec_sum'] += reading[9]  # ec

    # حساب المتوسطات
    daily_averages = []
    for day_data in daily_readings.values():
        count = day_data['readings_count']
        daily_averages.append({
            'day': day_data['day'],
            'month': day_data['month'],
            'year': day_data['year'],
            'readings_count': count,
            'ph': round(day_data['ph_sum'] / count, 2),
            'temperature': round(day_data['temperature_sum'] / count, 2),
            'humidity': round(day_data['humidity_sum'] / count, 2),
            'salt': round(day_data['salt_sum'] / count, 2),
            'light': round(day_data['light_sum'] / count, 2),
            'ec': round(day_data['ec_sum'] / count, 2)
        })
    
    return sorted(daily_averages, key=lambda x: (x['year'], x['month'], x['day']))

@a.app.route('/readings/daily', methods=['POST'])
def get_daily_readings():
    try:
        data = a.request.get_json()
        if not data or 'date' not in data:
            return a.jsonify({
                'status': 'error',
                'message': 'date parameter is required in request body (YYYY-MM-DD format)'
            }), 400
            
        date_str = data['date']
        date_obj = a.datetime.strptime(date_str, '%Y-%m-%d')
        day = date_obj.day
        month = date_obj.month
        year = date_obj.year

        cur = a.conn.cursor()

        query = """
            SELECT day, month, year, time, ph, temperature, humidity, salt, light, ec
            FROM sensor_readings.readings
            WHERE day = %s AND month = %s AND year = %s
            ORDER BY time;
        """
        cur.execute(query, (day, month, year))
        
        readings = cur.fetchall()
        
        # تجهيز القراءات التفصيلية
        detailed_readings = []
        for reading in readings:
            detailed_readings.append({
                'time': reading[3].hour if hasattr(reading[3], 'hour') else int(str(reading[3]).split(':')[0]),
                'ph': reading[4],
                'temperature': reading[5],
                'humidity': reading[6],
                'salt': reading[7],
                'light': reading[8],
                'ec': reading[9]
            })
        
        # حساب المتوسطات
        if readings:
            ph_values = [r[4] for r in readings if r[4] is not None]
            temp_values = [r[5] for r in readings if r[5] is not None]
            humidity_values = [r[6] for r in readings if r[6] is not None]
            salt_values = [r[7] for r in readings if r[7] is not None]
            light_values = [r[8] for r in readings if r[8] is not None]
            ec_values = [r[9] for r in readings if r[9] is not None]
            
            averages = {
                'ph': round(sum(ph_values) / len(ph_values), 2) if ph_values else 0,
                'temperature': round(sum(temp_values) / len(temp_values), 2) if temp_values else 0,
                'humidity': round(sum(humidity_values) / len(humidity_values), 2) if humidity_values else 0,
                'salt': round(sum(salt_values) / len(salt_values), 2) if salt_values else 0,
                'light': round(sum(light_values) / len(light_values), 2) if light_values else 0,
                'ec': round(sum(ec_values) / len(ec_values), 2) if ec_values else 0
            }
        else:
            averages = {
                'ph': 0,
                'temperature': 0,
                'humidity': 0,
                'salt': 0,
                'light': 0,
                'ec': 0
            }

        response = {
            'status': 'success',
            'date': {
                'day': day,
                'month': month,
                'year': year
            },
            'total_readings': len(readings),
            'readings': detailed_readings,  # القراءات التفصيلية
            'daily_average': averages      # متوسطات اليوم
        }
        
        cur.close()
        return a.jsonify(response)
    except Exception as e:
        print("❌ Error in get_today_readings:", e)
        return a.jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@a.app.route('/readings/monthly', methods=['POST'])
def get_month_readings():
    try:
        data = a.request.get_json()
        if not data or 'month' not in data or 'year' not in data:
            return a.jsonify({
                'status': 'error',
                'message': 'month and year parameters are required in request body'
            }), 400
            
        month = int(data['month'])
        year = int(data['year'])
    except ValueError:
        return a.jsonify({'status': 'error', 'message': 'Invalid month or year format'}), 400

    cur = a.conn.cursor()

    query = """
        SELECT day, month, year, time, ph, temperature, humidity, salt, light, ec
        FROM sensor_readings.readings
        WHERE month = %s AND year = %s
        ORDER BY day, time;
    """
    cur.execute(query, (month, year))
    readings = cur.fetchall()

    # حساب المتوسطات اليومية
    daily_averages = calculate_daily_averages(readings)

    # حساب الإحصائيات
    stats = {
        'month_name': a.calendar.month_name[month],
        'year': year,
        'total_days': len(daily_averages),
        'total_readings': len(readings)
    }

    response = {
        'status': 'success',
        'count': len(daily_averages),
        'data': daily_averages,
        'statistics': stats
    }
    
    cur.close()
    return a.jsonify(response)

@a.app.route('/readings/between', methods=['POST'])
def get_readings_between_dates():
    data = a.request.get_json()
    if not data or 'start_date' not in data or 'end_date' not in data:
        return a.jsonify({
            'status': 'error',
            'message': 'start_date and end_date are required in request body (YYYY-MM-DD format)'
        }), 400

    start_date = data['start_date']
    end_date = data['end_date']

    try:
        start_date_obj = a.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = a.datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_date_obj < start_date_obj:
            return a.jsonify({
                'status': 'error',
                'message': 'end_date cannot be earlier than start_date'
            }), 400
            
    except ValueError:
        return a.jsonify({
            'status': 'error',
            'message': 'Invalid date format. Please use YYYY-MM-DD'
        }), 400

    cur = a.conn.cursor()

    query = """
        SELECT day, month, year, time, ph, temperature, humidity, salt, light, ec
        FROM sensor_readings.readings
        WHERE (year > %s OR (year = %s AND month > %s) OR (year = %s AND month = %s AND day >= %s))
          AND (year < %s OR (year = %s AND month < %s) OR (year = %s AND month = %s AND day <= %s))
        ORDER BY year, month, day, time;
    """
    
    cur.execute(query, (
        start_date_obj.year, start_date_obj.year, start_date_obj.month, 
        start_date_obj.year, start_date_obj.month, start_date_obj.day,
        end_date_obj.year, end_date_obj.year, end_date_obj.month, 
        end_date_obj.year, end_date_obj.month, end_date_obj.day
    ))

    readings = cur.fetchall()

    # حساب المتوسطات اليومية
    daily_averages = calculate_daily_averages(readings)

    # حساب الإحصائيات
    date_diff = (end_date_obj - start_date_obj).days + 1
    stats = {
        'date_range': {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': date_diff,
            'days_with_readings': len(daily_averages),
            'total_readings': len(readings)
        }
    }

    response = {
        'status': 'success',
        'count': len(daily_averages),
        'data': daily_averages,
        'statistics': stats
    }

    cur.close()
    return a.jsonify(response)

@a.app.route('/get_stage_nutrients', methods=['GET'])
def get_stage_nutrients():
    try:
        # حساب عدد الأيام من قاعدة البيانات
        cur = a.conn.cursor()
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
            
        # تحديد المرحلة الحالية
        current_stage = determine_plant_stage(days_passed)
        if not current_stage:
            return a.jsonify({
                'status': 'error',
                'message': 'Could not determine plant stage'
            }), 404

        # تحديد نسب NPK بناءً على المرحلة
        npk_ratios = {
            "Seed Germination and Early Seedling": "1:3:2",
            "Vegetative Growth": "3:2:2",
            "Flowering": "1:2:2",
            "Fruiting": "1:2:4",
            "Harvesting": "1:3:7",
            "Post-Harvest": "1:1:1"
        }
            
        # جلب القيم من قاعدة البيانات
        query = """
            SELECT 
                stage,
                ec_min, ec_max,
                ph_min, ph_max,
                iron_ppm,
                calcium_ppm,
                magnesium_ppm,
                boron_ppm,
                zinc_ppm
            FROM tasmeed.tasmeed_iot
            WHERE stage = %s
            LIMIT 1
        """
        
        cur.execute(query, (current_stage,))
        result = cur.fetchone()
        cur.close()
        
        if result is None:
            return a.jsonify({
                'status': 'error',
                'message': 'No nutrient data found for this stage'
            }), 404

        def parse_range_and_get_optimal(value_str):
            """تحويل السترينج إلى قيمتين وحساب القيمة المثالية"""
            try:
                if isinstance(value_str, (int, float)):
                    return float(value_str), float(value_str), float(value_str)
                if '-' in str(value_str):
                    min_val, max_val = map(float, str(value_str).split('-'))
                    return min_val, max_val, round((min_val + max_val) / 2, 2)
                return float(value_str), float(value_str), float(value_str)
            except:
                return 0, 0, 0
            
        # حساب القيم المثالية (المتوسطة) لكل عنصر
        ec_min, ec_max = float(result[1]), float(result[2])
        ph_min, ph_max = float(result[3]), float(result[4])
        
        # حساب القيم المثالية مع إضافة عنصر عشوائي
        ec_mid = (ec_max + ec_min) / 2
        ec_range = (ec_max - ec_min) * 0.2  # 20% من المدى الكلي
        ec_optimal = round(a.random.uniform(ec_mid - ec_range, ec_mid + ec_range), 2)
        ec_optimal = max(ec_min, min(ec_max, ec_optimal))  # التأكد من عدم تجاوز الحدود
        
        ph_mid = (ph_max + ph_min) / 2
        ph_range = (ph_max - ph_min) * 0.2  # 20% من المدى الكلي
        ph_optimal = round(a.random.uniform(ph_mid - ph_range, ph_mid + ph_range), 2)
        ph_optimal = max(ph_min, min(ph_max, ph_optimal))  # التأكد من عدم تجاوز الحدود
        
        # حساب القيم للعناصر الكيميائية
        iron_min, iron_max, iron_optimal = parse_range_and_get_optimal(result[5])
        calcium_min, calcium_max, calcium_optimal = parse_range_and_get_optimal(result[6])
        magnesium_min, magnesium_max, magnesium_optimal = parse_range_and_get_optimal(result[7])
        boron_min, boron_max, boron_optimal = parse_range_and_get_optimal(result[8])
        zinc_min, zinc_max, zinc_optimal = parse_range_and_get_optimal(result[9])
            
        # تنظيم البيانات في شكل مناسب للفرونت
        nutrients_data = {
            'status': 'success',
            'stage': result[0],
            'days_passed': days_passed,
            'nutrients': {
                'ec': {
                    'value': ec_optimal,
                    'unit': 'mS/cm'
                },
                'ph': {
                    'value': ph_optimal,
                    'unit': 'pH'
                },
                'elements': {
                    'iron': {
                        'min': iron_min,
                        'optimal': iron_optimal,
                        'max': iron_max,
                        'unit': 'ppm'
                    },
                    'calcium': {
                        'min': calcium_min,
                        'optimal': calcium_optimal,
                        'max': calcium_max,
                        'unit': 'ppm'
                    },
                    'magnesium': {
                        'min': magnesium_min,
                        'optimal': magnesium_optimal,
                        'max': magnesium_max,
                        'unit': 'ppm'
                    },
                    'boron': {
                        'min': boron_min,
                        'optimal': boron_optimal,
                        'max': boron_max,
                        'unit': 'ppm'
                    },
                    'zinc': {
                        'min': zinc_min,
                        'optimal': zinc_optimal,
                        'max': zinc_max,
                        'unit': 'ppm'
                    },
                    
                    'npk': npk_ratios[current_stage]
                }
            }
        }
        
        return a.jsonify(nutrients_data)
        
    except Exception as e:
        print("❌ Error in get_stage_nutrients:", e)
        return a.jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@a.app.route('/actions/daily', methods=['POST'])
def get_daily_actions():
    try:
        data = a.request.get_json()
        if not data or 'date' not in data:
            return a.jsonify({
                'status': 'error',
                'message': 'date parameter is required in request body (YYYY-MM-DD format)'
            }), 400
            
        date_str = data['date']
        date_obj = a.datetime.strptime(date_str, '%Y-%m-%d')
        day = date_obj.day
        month = date_obj.month
        year = date_obj.year

        cur = a.conn.cursor()

        query = """
            SELECT action_time, action_day, action_month, action_year, action_type
            FROM sensor_readings.actions
            WHERE action_day = %s AND action_month = %s AND action_year = %s
            ORDER BY action_time;
        """
        cur.execute(query, (day, month, year))
        actions = cur.fetchall()
        
        formatted_actions = []
        for action in actions:
            formatted_actions.append({
                'time': action[0].hour if hasattr(action[0], 'hour') else int(str(action[0]).split(':')[0]),
                'type': action[4]
            })

        response = {
            'status': 'success',
            'date': {
                'day': day,
                'month': month,
                'year': year
            },
            'total_actions': len(formatted_actions),
            'actions': formatted_actions
        }
        
        cur.close()
        return a.jsonify(response)
        
    except Exception as e:
        print("❌ Error in get_daily_actions:", e)
        return a.jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@a.app.route('/actions/monthly', methods=['POST'])
def get_monthly_actions():
    try:
        data = a.request.get_json()
        if not data or 'month' not in data or 'year' not in data:
            return a.jsonify({
                'status': 'error',
                'message': 'month and year parameters are required in request body'
            }), 400
            
        month = int(data['month'])
        year = int(data['year'])
    except ValueError:
        return a.jsonify({'status': 'error', 'message': 'Invalid month or year format'}), 400

    cur = a.conn.cursor()

    query = """
        SELECT action_time, action_day, action_month, action_year, action_type
        FROM sensor_readings.actions
        WHERE action_month = %s AND action_year = %s
        ORDER BY action_day, action_time;
    """
    cur.execute(query, (month, year))
    actions = cur.fetchall()

    # تنظيم الأحداث حسب اليوم
    daily_actions = {}
    for action in actions:
        day = action[1]
        if day not in daily_actions:
            daily_actions[day] = []
        
        daily_actions[day].append({
            'time': action[0].hour if hasattr(action[0], 'hour') else int(str(action[0]).split(':')[0]),
            'type': action[4]
        })

    # تحويل القاموس إلى قائمة مرتبة
    formatted_days = []
    for day in sorted(daily_actions.keys()):
        formatted_days.append({
            'day': day,
            'actions_count': len(daily_actions[day]),
            'actions': daily_actions[day]
        })

    response = {
        'status': 'success',
        'month': month,
        'year': year,
        'total_days': len(formatted_days),
        'total_actions': len(actions),
        'days': formatted_days
    }
    
    cur.close()
    return a.jsonify(response)

@a.app.route('/actions/between', methods=['POST'])
def get_actions_between_dates():
    data = a.request.get_json()
    if not data or 'start_date' not in data or 'end_date' not in data:
        return a.jsonify({
            'status': 'error',
            'message': 'start_date and end_date are required in request body (YYYY-MM-DD format)'
        }), 400

    start_date = data['start_date']
    end_date = data['end_date']

    try:
        start_date_obj = a.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = a.datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_date_obj < start_date_obj:
            return a.jsonify({
                'status': 'error',
                'message': 'end_date cannot be earlier than start_date'
            }), 400
            
    except ValueError:
        return a.jsonify({
            'status': 'error',
            'message': 'Invalid date format. Please use YYYY-MM-DD'
        }), 400

    cur = a.conn.cursor()

    query = """
        SELECT action_time, action_day, action_month, action_year, action_type
        FROM sensor_readings.actions
        WHERE (action_year > %s OR (action_year = %s AND action_month > %s) OR (action_year = %s AND action_month = %s AND action_day >= %s))
          AND (action_year < %s OR (action_year = %s AND action_month < %s) OR (action_year = %s AND action_month = %s AND action_day <= %s))
        ORDER BY action_year, action_month, action_day, action_time;
    """
    
    cur.execute(query, (
        start_date_obj.year, start_date_obj.year, start_date_obj.month, 
        start_date_obj.year, start_date_obj.month, start_date_obj.day,
        end_date_obj.year, end_date_obj.year, end_date_obj.month, 
        end_date_obj.year, end_date_obj.month, end_date_obj.day
    ))

    actions = cur.fetchall()

    # تنظيم الأحداث حسب اليوم
    daily_actions = {}
    for action in actions:
        day_key = f"{action[3]}-{action[2]:02d}-{action[1]:02d}"  # YYYY-MM-DD
        if day_key not in daily_actions:
            daily_actions[day_key] = []
        
        daily_actions[day_key].append({
            'time': action[0].hour if hasattr(action[0], 'hour') else int(str(action[0]).split(':')[0]),
            'type': action[4]
        })

    # تحويل القاموس إلى قائمة مرتبة
    formatted_days = []
    for day in sorted(daily_actions.keys()):
        formatted_days.append({
            'date': day,
            'actions_count': len(daily_actions[day]),
            'actions': daily_actions[day]
        })

    response = {
        'status': 'success',
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        },
        'total_days': len(formatted_days),
        'total_actions': len(actions),
        'days': formatted_days
    }

    cur.close()
    return a.jsonify(response)

@a.app.route('/readings/latest', methods=['GET'])
def get_latest_readings1():
    try:
        cur = a.conn.cursor()

        query = """
            SELECT day, month, year, time, ph, temperature, humidity, salt, light, ec
            FROM sensor_readings.readings
            ORDER BY year DESC, month DESC, day DESC, time DESC
            LIMIT 1;
        """
        cur.execute(query)
        reading = cur.fetchone()
        
        if not reading:
            return a.jsonify({
                'status': 'error',
                'message': 'No readings found'
            }), 404

        response = {
            'status': 'success',
            'data': {
                'date': {
                    'day': reading[0],
                    'month': reading[1],
                    'year': reading[2]
                },
                'time': reading[3].hour if hasattr(reading[3], 'hour') else int(str(reading[3]).split(':')[0]),
                'readings': {
                    'ph': reading[4],
                    'temperature': reading[5],
                    'humidity': reading[6],
                    'salt': reading[7],
                    'light': reading[8],
                    'ec': reading[9]
                }
            }
        }
        
        cur.close()
        return a.jsonify(response)
        
    except Exception as e:
        print("❌ Error in get_latest_readings:", e)
        return a.jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
        

@a.app.route('/readings/latest/water', methods=['GET'])
def get_latest_readings():
    try:
        cur = a.conn.cursor()
        
        cur.execute("SELECT water FROM sensor_readings.readings ORDER BY id DESC LIMIT 1;")
        result = cur.fetchone()

        cur.close()
        a.conn.close()

        if result:
            return a.jsonify({'water': result[0]})
        else:
            return a.jsonify({'message': 'No data found'}), 404

    except Exception as e:
        return a.jsonify({'error': str(e)}), 500        