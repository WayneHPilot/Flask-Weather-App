from flask import Flask, render_template, request, jsonify
import os
import requests
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import numpy as np
from dotenv import load_dotenv

# Use non-interactive backend for Matplotlib
matplotlib.use('Agg')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='static')

API_KEY = os.getenv("VISUAL_CROSSING_API_KEY")
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/get_weather', methods=['POST'])
def get_weather():
	city = request.form.get('city')
	if not city:
		return jsonify({'error': 'Please enter a city name'})

	try:
		# Request weather data from API
		url = f"{BASE_URL}/{city}/next24hours?key={API_KEY}&contentType=json"
		logging.info(f"Requesting data from: {url.replace(API_KEY, 'API_KEY_HIDDEN')}")
		response = requests.get(url)

		# Check API response status
		if response.status_code != 200:
			return jsonify({'error': f"API Error: {response.status_code} - {response.text}"})

		# Parse JSON response
		try:
			data = response.json()
		except Exception as e:
			logging.error(f"Failed to parse API response: {str(e)}")
			return jsonify({'error': 'Invalid API response format'})

		# Ensure required fields exist
		current = data.get('currentConditions', {})
		if not current:
			logging.warning("Missing 'currentConditions' in API response")
			return jsonify({'error': 'Weather API returned unexpected data.'})

		# Extract weather details with default fallbacks
		def get_data(field, default="N/A"):
			return current.get(field, default)

		current_temp = get_data('temp')
		humidity = get_data('humidity')
		wind_speed = get_data('windspeed')
		conditions = get_data('conditions')

		# Convert temperature to Celsius if available
		if isinstance(current_temp, (int, float)):
			current_temp = round((current_temp - 32) * 5/9, 2)

		# Fetch hourly forecast data
		hours_data = data.get('days', [{}])[0].get('hours', [])
		if not hours_data:
			logging.warning("No hourly data available")
			return jsonify({
				'city': city.title(),
				'temperature': current_temp,
				'humidity': humidity,
				'wind_speed': wind_speed,
				'conditions': conditions,
				'error': 'No hourly temperature data available.'
			})

		# Extract hours and temperatures
		hours, temps = [], []
		for hour_data in hours_data:
			try:
				hour_time = datetime.strptime(hour_data.get('datetime', ''), "%H:%M:%S").strftime("%H:%M")
				temp = hour_data.get('temp')

				# Convert Fahrenheit to Celsius
				if temp is not None:
					temp = round((temp - 32) * 5/9, 2)

				hours.append(hour_time)
				temps.append(temp)
			except Exception as e:
				logging.error(f"Error processing hour data: {e}")
				continue

		if not hours or not temps:
			logging.error("No valid temperature data found for graphing")
			return jsonify({
				'city': city.title(),
				'temperature': current_temp,
				'humidity': humidity,
				'wind_speed': wind_speed,
				'conditions': conditions,
				'error': 'Could not generate temperature graph due to missing data.'
			})

		# Generate temperature graph
		plt.figure(figsize=(10, 5))
		plt.plot(hours, temps, marker='o', linestyle='-', color='#007bff')
		plt.title(f'Temperature Throughout the Day in {city.title()}')
		plt.xlabel('Time')
		plt.ylabel('Temperature (°C)')
		plt.grid(True, linestyle='--', alpha=0.7)
		plt.xticks(rotation=45)

		# Limit x-axis labels for readability
		if len(hours) > 12:
			plt.xticks(np.arange(0, len(hours), 2))

		plt.tight_layout()

		# Save graph as base64 string
		buffer = io.BytesIO()
		plt.savefig(buffer, format='png')
		buffer.seek(0)
		image_png = buffer.getvalue()
		buffer.close()
		plt.close()

		graph = base64.b64encode(image_png).decode('utf-8')

		# Return weather data with graph
		return jsonify({
			'city': city.title(),
			'temperature': current_temp,
			'humidity': humidity,
			'wind_speed': wind_speed,
			'conditions': conditions,
			'graph': graph
		})

	except Exception as e:
		logging.error(f"Exception occurred: {str(e)}", exc_info=True)
		return jsonify({'error': f'Error fetching weather data: {str(e)}'})


if __name__ == '__main__':
	app.run(debug=True)
