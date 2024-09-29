import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import config  # Importing credentials from config.py

# Mapping Weather Symbol IDs to Descriptions and Icons (using emojis as placeholders)
weather_symbol_map = {
    0: ("A weather symbol could not be determined", "❓"),
    1: ("Clear sky", "☀️"),
    101: ("Clear sky (night)", "🌕"),
    2: ("Light clouds", "🌤"),
    102: ("Light clouds (night)", "🌥"),
    3: ("Partly cloudy", "⛅"),
    103: ("Partly cloudy (night)", "☁️"),
    4: ("Cloudy", "☁️"),
    104: ("Cloudy (night)", "☁️"),
    5: ("Rain", "🌧"),
    105: ("Rain (night)", "🌧"),
    6: ("Rain and snow / sleet", "🌨"),
    106: ("Rain and snow / sleet (night)", "🌨"),
    7: ("Snow", "❄️"),
    107: ("Snow (night)", "❄️"),
    8: ("Rain shower", "🌦"),
    108: ("Rain shower (night)", "🌦"),
    9: ("Snow shower", "🌨"),
    109: ("Snow shower (night)", "🌨"),
    10: ("Sleet shower", "🌨"),
    110: ("Sleet shower (night)", "🌨"),
    11: ("Light fog", "🌫️"),
    111: ("Light fog (night)", "🌫️"),
    12: ("Dense fog", "🌫️"),
    112: ("Dense fog (night)", "🌫️"),
    13: ("Freezing rain", "🌧❄️"),
    113: ("Freezing rain (night)", "🌧❄️"),
    14: ("Thunderstorms", "⛈"),
    114: ("Thunderstorms (night)", "⛈"),
    15: ("Drizzle", "🌧"),
    115: ("Drizzle (night)", "🌧"),
    16: ("Sandstorm", "🌪️"),
    116: ("Sandstorm (night)", "🌪️")
}

# McDonough, GA coordinates
LATITUDE = '33.4473'
LONGITUDE = '-84.1469'

# RSS feed URLs
RSS_FEED_NHC = "https://www.nhc.noaa.gov/nhc_at1.xml"
RSS_FEED_SPC = "https://www.spc.noaa.gov/products/spcwwrss.xml"

# Function to fetch the first description from an RSS feed
def fetch_first_description_from_rss(url):
    try:
        response = requests.get(url)
        # Parse the XML response
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()
        
        # Find the first description field in the feed
        for item in root.findall(".//item"):
            description = item.find("description")
            if description is not None:
                return description.text
        return "No description available."
    except Exception as e:
        return f"Error fetching data: {e}"

# Function to fetch weather data from Meteomatics API
def fetch_weather_data(latitude, longitude):
    # Define the parameters with correct Meteomatics codes
    params = {
        'temperature': f"t_2m:C/{latitude},{longitude}",
        'weather_symbol': f"weather_symbol_1h:idx/{latitude},{longitude}",
        'heavy_rain_warning': f"precip_1h:mm/{latitude},{longitude}",  # Precipitation warning
        'air_quality': f"pm2p5:ugm3/{latitude},{longitude}",
    }
    
    weather_data = {}
    
    # Loop over the parameters and request each
    for param, endpoint in params.items():
        try:
            url = f"https://api.meteomatics.com/{datetime.utcnow().isoformat()}Z/{endpoint}/json"
            response = requests.get(url, auth=(config.USERNAME, config.PASSWORD))
            response.raise_for_status()
            # Parse the JSON response
            data = response.json()
            weather_data[param] = data['data'][0]['coordinates'][0]['dates'][0]['value']
        except requests.exceptions.HTTPError as http_err:
            weather_data[param] = f"Error fetching {param}: {http_err}"
        except Exception as err:
            weather_data[param] = f"Error fetching {param}: {err}"
    
    return weather_data

# Function to get the weather symbol description and icon
def get_weather_symbol_description(symbol_id):
    return weather_symbol_map.get(symbol_id, ("Unknown symbol", "❓"))

# Streamlit app
def main():
    st.title("Jim's Meteomatics Dashboard")
    
    st.title("NHC Latest")
    
    # Fetch the first description from NHC RSS feed
    description_nhc = fetch_first_description_from_rss(RSS_FEED_NHC)
    
    # Add the hurricane/tropical storm emoji and wrap the description
    description_with_emoji = f"🌪️ {description_nhc}"
    
    # Display the NHC description with a red background bar
    st.markdown(
        f"""
        <div style="background-color: #FF0000; padding: 10px; margin-bottom: 10px;">
            <p style="color: white; text-align: center;">{description_with_emoji}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch the first description from SPC RSS feed
    description_spc = fetch_first_description_from_rss(RSS_FEED_SPC)
    
    # Add an icon for storm warning and wrap the description
    description_spc_with_emoji = f"⛈️ {description_spc}"
    
    # Display the SPC description with a blue background bar
    st.markdown(
        f"""
        <div style="background-color: #007BFF; padding: 10px; margin-bottom: 10px;">
            <p style="color: white; text-align: center;">{description_spc_with_emoji}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Fetch weather data for McDonough, GA
    weather_data = fetch_weather_data(LATITUDE, LONGITUDE)
    
    # Display the current weather information
    st.header("Current Weather in McDonough, GA:")
    st.write(f"**Temperature**: {weather_data.get('temperature')} °C")

    # Get the weather symbol ID and corresponding description and icon
    weather_symbol_id = int(weather_data.get('weather_symbol', 0))  # default to 0 if missing
    symbol_description, symbol_icon = get_weather_symbol_description(weather_symbol_id)
    
    st.write(f"**Weather Symbol**: {symbol_icon} {symbol_description}")
    st.write(f"**Heavy Rain Warning**: {weather_data.get('heavy_rain_warning')} mm")
    st.write(f"**Air Quality (PM2.5)**: {weather_data.get('air_quality')} µg/m³")

if __name__ == "__main__":
    main()
