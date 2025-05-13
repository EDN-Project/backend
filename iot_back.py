import app as a

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
                'light_sum': 0
            }
        
        daily_readings[day_key]['readings_count'] += 1
        daily_readings[day_key]['ph_sum'] += reading[4]  # ph
        daily_readings[day_key]['temperature_sum'] += reading[5]  # temperature
        daily_readings[day_key]['humidity_sum'] += reading[6]  # humidity
        daily_readings[day_key]['salt_sum'] += reading[7]  # salt
        daily_readings[day_key]['light_sum'] += reading[8]  # light

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
            'light': round(day_data['light_sum'] / count, 2)
        })
    
    return sorted(daily_averages, key=lambda x: (x['year'], x['month'], x['day']))

@a.app.route('/readings/daily', methods=['GET'])
def get_today_readings():
    now = a.datetime.now()
    day = now.day
    month = now.month
    year = now.year

    cur = a.conn.cursor()

    query = """
        SELECT day, month, year, time, ph, temperature, humidity, salt, light
        FROM raeding
        WHERE day = %s AND month = %s AND year = %s
        ORDER BY time;
    """
    cur.execute(query, (day, month, year))
    
    columns = ['day', 'month', 'year', 'time', 'ph', 'temperature', 'humidity', 'salt', 'light']
    readings = cur.fetchall()
    
    return a.jsonify(format_readings(readings, columns))

@a.app.route('/readings/monthly', methods=['GET'])
def get_month_readings():
    try:
        month = int(a.request.args.get('month', a.datetime.now().month))
        year = int(a.request.args.get('year', a.datetime.now().year))
    except ValueError:
        return a.jsonify({'status': 'error', 'message': 'Invalid month or year format'}), 400

    cur = a.conn.cursor()

    query = """
        SELECT day, month, year, time, ph, temperature, humidity, salt, light
        FROM raeding
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

@a.app.route('/readings/between', methods=['GET'])
def get_readings_between_dates():
    start_date = a.request.args.get('start_date')
    end_date = a.request.args.get('end_date')

    if not start_date or not end_date:
        return a.jsonify({
            'status': 'error',
            'message': 'Please provide start_date and end_date in YYYY-MM-DD format'
        }), 400

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
        SELECT day, month, year, time, ph, temperature, humidity, salt, light
        FROM raeding
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

if __name__ == '__main__':
    a.app.run(debug=True)