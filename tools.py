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
    Weather Tool: supports current, yesterday, and past 7 days history or 7-day forecast.
    Returns a machine-friendly JSON prefixed with `__JSON__:` followed by a human summary.
    Example queries:
      - "weather in Bangalore"
      - "yesterday weather in Delhi"
      - "past 7 days weather in Bangalore"
      - "7-day forecast for Mumbai"
    """
    try:
        import re, json
        q = query.strip()
        q_lower = q.lower()

        if not WEATHER_API_KEY:
            return "❌ Weather API Error: WEATHER_API_KEY not set"

        is_forecast = "forecast" in q_lower or "7-day" in q_lower
        is_yesterday = "yesterday" in q_lower
        is_past7 = any(k in q_lower for k in ("past 7", "last 7", "past7", "last7", "history", "past week"))

        # extract city after 'in' or 'at' or 'for'
        m = re.search(r"\b(?:in|at|for)\s+([a-zA-Z ]+)$", q_lower)
        if m:
            city = m.group(1).strip().title()
        else:
            # fallback: look for common city name words in the query
            tokens = re.findall(r"[a-zA-Z]+", q_lower)
            city = None
            for t in tokens[::-1]:
                if t not in {"weather","in","for","the","on","of","past","last","7","days","yesterday","forecast"}:
                    city = t.title()
                    break
            if not city:
                city = q.strip().title()

        # historical: past 7 days
        if is_past7:
            records = []
            for i in range(0, 7):
                dt = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
                url = f"http://api.weatherapi.com/v1/history.json?key={WEATHER_API_KEY}&q={city}&dt={dt}"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                day = data.get("forecast", {}).get("forecastday", [None])[0]
                if not day:
                    continue
                rec = {
                    "date": dt,
                    "avgtemp_c": day["day"].get("avgtemp_c"),
                    "condition": day["day"].get("condition", {}).get("text")
                }
                records.append(rec)
            if not records:
                return f"❌ Could not fetch past 7 days weather for {city}."
            out = {"type": "weather", "scope": "past7", "city": city, "records": records}
            human = "\n".join([f"{r['date']}: {r['avgtemp_c']}°C, {r['condition']}" for r in records])
            return f"__JSON__:{json.dumps(out)}\n\n📊 Past 7 Days for {city}:\n{human}"

        if is_yesterday:
            yday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"http://api.weatherapi.com/v1/history.json?key={WEATHER_API_KEY}&q={city}&dt={yday}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            day = data.get("forecast", {}).get("forecastday", [None])[0]
            if not day:
                return f"❌ Could not fetch yesterday's weather for {city}."
            avg_temp = day["day"].get("avgtemp_c")
            cond = day["day"].get("condition", {}).get("text")
            out = {"type": "weather", "scope": "yesterday", "city": city, "date": yday, "avgtemp_c": avg_temp, "condition": cond}
            return f"__JSON__:{json.dumps(out)}\n\n📆 Yesterday in {city} ({yday}): {avg_temp}°C, {cond}"

        if is_forecast:
            url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            days = data.get("forecast", {}).get("forecastday", [])
            if not days:
                return f"❌ Could not fetch forecast for {city}."
            records = []
            for day in days:
                records.append({"date": day.get("date"), "avgtemp_c": day.get("day", {}).get("avgtemp_c"), "condition": day.get("day", {}).get("condition", {}).get("text")})
            out = {"type": "weather", "scope": "forecast7", "city": city, "records": records}
            human = "\n".join([f"{d['date']}: {d['avgtemp_c']}°C, {d['condition']}" for d in records])
            return f"__JSON__:{json.dumps(out)}\n\n📅 7‑Day Forecast for {city}:\n{human}"

        # current
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        temp = data.get("current", {}).get("temp_c")
        cond = data.get("current", {}).get("condition", {}).get("text")
        out = {"type": "weather", "scope": "current", "city": city, "temp_c": temp, "condition": cond}
        return f"__JSON__:{json.dumps(out)}\n\n🌤️ Current Weather in {city}: {temp}°C, {cond}"

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
