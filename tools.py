import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@tool
def tool1_weather(query: str) -> str:
    """
    Weather Tool: current, yesterday, or 7-day forecast.
    Example queries:
      - "weather in Bangalore"
      - "yesterday weather in Delhi"
      - "7-day forecast for Mumbai"
    """
    try:
        import re
        q = query.lower()

        is_forecast = "forecast" in q or "7-day" in q
        is_yesterday = "yesterday" in q

        cities = re.findall(r"(in|at|of)?\s*([A-Z][a-z]+(?: [A-Z][a-z]+)?)", query)
        city = cities[0][1] if cities else query.strip()

        if is_yesterday:
            yday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"http://api.weatherapi.com/v1/history.json?key={WEATHER_API_KEY}&q={city}&dt={yday}"
            data = requests.get(url, timeout=10).json()
            avg_temp = data["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
            cond = data["forecast"]["forecastday"][0]["day"]["condition"]["text"]
            return f"📆 Yesterday in {city} ({yday}): {avg_temp}°C, {cond}"

        elif is_forecast:
            url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7"
            data = requests.get(url, timeout=10).json()
            result = f"📅 7‑Day Forecast for {city}:\n"
            for day in data["forecast"]["forecastday"]:
                result += f"{day['date']}: {day['day']['condition']['text']}, Avg {day['day']['avgtemp_c']}°C\n"
            return result.strip()

        else:
            url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
            data = requests.get(url, timeout=10).json()
            temp = data["current"]["temp_c"]
            cond = data["current"]["condition"]["text"]
            return f"🌤️ Current Weather in {city}: {temp}°C, {cond}"

    except Exception as e:
        return f"❌ Weather API Error: {str(e)}"


@tool
def tool2_stock(query: str) -> str:
    """
    Stock Tool using Alpha Vantage.
    Supports current price and historical daily prices.
    Example queries:
      - "TCS stock price"
      - "ORCL stock price last week"
    """
    try:
        import re
        q = query.lower()
        parts = re.findall(r"([a-zA-Z.]+)", q)
        if not parts:
            return "❌ No stock symbol found in query."
        symbol = parts[0].upper()

        if "last week" in q or "historical" in q:
            url = (
                f"https://www.alphavantage.co/query?"
                f"function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            )
            data = requests.get(url, timeout=10).json()
            ts = data.get("Time Series (Daily)")
            if not ts:
                return f"❌ Could not fetch historical data for {symbol}."
            dates = sorted(ts.keys(), reverse=True)[:7]
            result = f"📊 Last 7 Days Prices for {symbol}:\n"
            for date in dates:
                close = ts[date]["4. close"]
                result += f"{date}: {close}\n"
            return result.strip()
        else:
            url = (
                f"https://www.alphavantage.co/query?"
                f"function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            )
            data = requests.get(url, timeout=10).json()
            quote = data.get("Global Quote")
            if not quote or not quote.get("05. price"):
                return f"❌ Could not fetch current price for {symbol}."
            price = quote["05. price"]
            return f"📈 Current Price of {symbol}: {price} USD"

    except Exception as e:
        return f"❌ Stock API Error: {str(e)}"


@tool
def tool3_general_qa(question: str) -> str:
    """
    General QA tool using Tavily API.
    """
    try:
        headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
        payload = {"query": question}
        url = "https://api.tavily.com/v1/search"
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if "answer" in data:
            return data["answer"]
        elif "results" in data and len(data["results"]) > 0:
            return data["results"][0]["snippet"]
        else:
            return f"(LLM fallback) {question}"
    except Exception as e:
        return f"❌ Tavily API Error: {str(e)}"
