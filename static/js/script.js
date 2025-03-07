document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');
    
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const city = document.getElementById('city').value.trim();
        if (!city) {
            showError('Please enter a city name');
            return;
        }
        
        // Show loading spinner
        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        
        // Create form data
        const formData = new FormData();
        formData.append('city', city);
        
        // Make API request
        fetch('/get_weather', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingDiv.style.display = 'none';
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Update the UI with weather data
            document.getElementById('city-name').textContent = data.city;
            
            // Format temperature with units
            const temp = data.temperature !== 'N/A' ? `${data.temperature}°C` : 'N/A';
            document.getElementById('temperature').textContent = temp;
            
            // Format humidity with percentage
            const humidity = data.humidity !== 'N/A' ? `${data.humidity}%` : 'N/A';
            document.getElementById('humidity').textContent = humidity;
            
            // Format wind speed with units
            const windSpeed = data.wind_speed !== 'N/A' ? `${data.wind_speed} km/h` : 'N/A';
            document.getElementById('wind-speed').textContent = windSpeed;
            
            document.getElementById('conditions').textContent = data.conditions;
            
            // Display the temperature graph if available
            if (data.graph) {
                document.getElementById('temp-graph').src = `data:image/png;base64,${data.graph}`;
                document.getElementById('temp-graph').style.display = 'block';
            } else {
                document.getElementById('temp-graph').style.display = 'none';
            }
            
            // Show results
            resultsDiv.style.display = 'grid';
        })
        .catch(error => {
            loadingDiv.style.display = 'none';
            showError('Failed to fetch weather data. Please try again.');
            console.error('Error:', error);
        });
    });
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
});