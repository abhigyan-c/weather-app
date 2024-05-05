from flask import Flask, request, jsonify
import requests
import sqlite3
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key'
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Initialize SQLite database
conn = sqlite3.connect('weather.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')



cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    city_name TEXT,
                    latitude REAL,
                    longitude REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')


conn.commit()

# WeatherAPI.com API credentials
API_KEY = '30528d9d4f60434ab03175129240105'
BASE_URL = 'http://api.weatherapi.com/v1'

#clear all
@app.route('/clear', methods=['DELETE'])
def clear():
    cursor.execute("DELETE from users")
    cursor.execute("DELETE from cities")
    conn.commit()
    return jsonify({'message': 'DB Cleared'})

# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    
    return jsonify({'message': 'User registered successfully'})

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user[2], password):
        access_token = create_access_token(identity=user[0])
        return jsonify({'access_token': access_token})
    else:
        return jsonify({'message': 'Invalid username or password'})

# Add city endpoint
@app.route('/add_city', methods=['POST'])
@jwt_required()
def add_city():
    current_user = get_jwt_identity()
    data = request.get_json()
    city_name = data.get('city_name')
    
    # Use geopy to get the latitude and longitude of the city
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(city_name)
    
    if location:
        latitude = location.latitude
        longitude = location.longitude
        
        # Store the city name, latitude, longitude, and user ID in the database
        cursor.execute("INSERT INTO cities (user_id, city_name, latitude, longitude) VALUES (?, ?, ?, ?)",
                       (current_user, city_name, latitude, longitude))
        conn.commit()
        
        return jsonify({'message': 'City added successfully'})
    else:
        return jsonify({'error': 'Failed to find coordinates for the city'}), 400


@app.route('/cities', methods=['GET'])
@jwt_required()
def get_cities():
    current_user = get_jwt_identity()
    
    cursor.execute("SELECT city_name, latitude, longitude FROM cities WHERE user_id=?", (current_user,))
    cities = cursor.fetchall()
    
    cities_with_coordinates = [{'city_name': city[0], 'latitude': city[1], 'longitude': city[2]} for city in cities]
    
    return jsonify({'cities': cities_with_coordinates})


# Weather endpoint
@app.route('/weather', methods=['GET'])
@jwt_required()
def get_weather():
    current_user = get_jwt_identity()
    
    cursor.execute("SELECT city_name FROM cities WHERE user_id=?", (current_user,))
    cities = cursor.fetchall()
    
    weather_data = []
    for city in cities:
        city_name = city[0]
        response = requests.get(f"{BASE_URL}/current.json?key={API_KEY}&q={city_name}")
        weather_data.append(response.json())
    
    return jsonify({'weather_data': weather_data})

# Historical Temperature endpoint
@app.route('/historical_temperature', methods=['GET'])
@jwt_required()
def get_historical_temperature():
    current_user = get_jwt_identity()
    
    cursor.execute("SELECT city_name FROM cities WHERE user_id=?", (current_user,))
    cities = cursor.fetchall()
    
    historical_temperature_data = []
    for city in cities:
        city_name = city[0]
        current_date = datetime.now().date()
        start_date = datetime.strptime('2024-05-01', '%Y-%m-%d').date()
        num_days = (current_date - start_date).days
        for i in range(num_days):
            current_date = start_date + timedelta(days=i)
            if current_date >= datetime.now().date():  # Skip if it's the current day
                continue
            formatted_date = current_date.strftime('%Y-%m-%d')
            try:
                response = requests.get(f"{BASE_URL}/history.json", params={'key': API_KEY, 'q': city_name, 'dt': formatted_date, 'tp': '1'})
                response.raise_for_status()
                historical_data = response.json()['forecast']['forecastday'][0]['hour']
                for hour_entry in historical_data:
                    historical_temperature_data.append({
                        'city': city_name,
                        'time': hour_entry['time'],
                        'temperature_c': hour_entry['temp_c'],  # Temperature in Celsius
                        'temperature_f': hour_entry['temp_f']   # Temperature in Fahrenheit
                    })
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for {formatted_date} in {city_name}: {e}")
    
    return jsonify({'historical_temperature': historical_temperature_data})

@app.route('/delete_city/<city_name>', methods=['DELETE'])
@jwt_required()
def delete_city(city_name):
    current_user = get_jwt_identity()
    
    # Perform deletion logic here using the city_name parameter
    cursor.execute("DELETE FROM cities where city_name=?", (city_name,))
    
    return jsonify({'message': 'City deleted successfully'})


if __name__ == '__main__':
    app.run(debug=True)
