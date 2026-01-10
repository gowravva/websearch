import os
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# ---------------- WEATHER TOOL ----------------
@tool
def tool1_weather(query: str) -> str:
    """
    Get weather information for a city.
    Supports:
    - current weather
    - yesterday's weather
    - 7-day weather forecast
    """
    try:
        q = query.lower()
        is_forecast = "forecast" in q or "7-day" in q
        is_yesterday = "yesterday" in q

        city_match = re.search(r"in\s+([a-zA-Z ]+)", query)
        city = city_match.group(1) if city_match else query

        if is_yesterday:
            date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"http://api.weatherapi.com/v1/history.json?key={WEATHER_API_KEY}&q={city}&dt={date}"
            data = requests.get(url, timeout=10).json()
            day = data["forecast"]["forecastday"][0]["day"]
            return f"📆 Yesterday in {city}: {day['avgtemp_c']}°C, {day['condition']['text']}"

        if is_forecast:
            url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7"
            data = requests.get(url, timeout=10).json()
            result = f"📅 7-Day Forecast for {city}:\n"
            for d in data["forecast"]["forecastday"]:
                result += f"{d['date']}: {d['day']['avgtemp_c']}°C, {d['day']['condition']['text']}\n"
            return result.strip()

        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
        data = requests.get(url, timeout=10).json()
        return f"🌤️ {city}: {data['current']['temp_c']}°C, {data['current']['condition']['text']}"

    except Exception as e:
        return f"❌ Weather error: {e}"


# ---------------- STOCK TOOL ----------------
@tool
def tool2_stock(query: str) -> str:
    """
    Fetch the latest stock price for a given stock symbol.
    Example queries:
    - TCS stock price
    - AAPL stock
    """
    try:
        symbol = re.findall(r"[A-Z]{2,}", query.upper())[0]
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        data = requests.get(url, timeout=10).json()
        price = data["Global Quote"]["05. price"]
        return f"📈 {symbol} stock price: {price} USD"
    except Exception as e:
        return f"❌ Stock error: {e}"


# ---------------- SEARCH TOOL ----------------
@tool
def tool3_general_search(query: str) -> str:
    """
    Answer general knowledge questions using web search.
    Uses Tavily search API to fetch summarized information.
    """
    try:
        results = tavily_client.search(query=query, max_results=3)
        answers = [f"- {r['content']}" for r in results["results"]]
        return "🔍 Search Results:\n" + "\n".join(answers)
    except Exception as e:
        return f"❌ Search error: {e}"
