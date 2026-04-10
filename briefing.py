import requests
import os
import json
import re
from datetime import datetime

NEIS_KEY = os.environ["NEIS_KEY"]
KAKAO_TOKEN = os.environ["KAKAO_TOKEN"]
KAKAO_CLIENT_ID = os.environ["KAKAO_CLIENT_ID"]
KAKAO_CLIENT_SECRET = os.environ["KAKAO_CLIENT_SECRET"]
KAKAO_REFRESH_TOKEN = os.environ["KAKAO_REFRESH_TOKEN"]

ATPT_CODE = "J10"
SCHOOL_CODE = "7530921"

def refresh_kakao_token():
    res = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,
        "refresh_token": KAKAO_REFRESH_TOKEN,
    })
    return res.json()["access_token"]

def get_meal():
    today = datetime.now().strftime("%Y%m%d")
    res = requests.get("https://open.neis.go.kr/hub/mealServiceDietInfo", params={
        "KEY": NEIS_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MLSV_YMD": today,
        "MMEAL_SC_CODE": "2",
    }).json()
    try:
        items = res["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"].split("<br/>")
        pattern = re.compile(r'\s*\([\d.,]+\)')
        cleaned = [pattern.sub('', i).strip() for i in items if i.strip()]
        return "\n".join("• " + item for item in cleaned)
    except:
        return None

def get_news():
    import xml.etree.ElementTree as ET
    categories = {
        "경제": "https://rss.naver.com/main/rss/news/economics.xml",
        "정치": "https://rss.naver.com/main/rss/news/politics.xml",
        "사회": "https://rss.naver.com/main/rss/news/society.xml",
    }
    result = ""
    for name, url in categories.items():
        try:
            res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(res.content)
            items = root.findall(".//item")[:2]
            titles = [item.find("title").text for item in items]
            result += name + "\n"
            result += "\n".join("• " + t for t in titles) + "\n\n"
        except:
            result += name + "\n• 불러오기 실패\n\n"
    return result.strip()
def get_weather():
    res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 37.35,
            "longitude": 127.12,
            "current": "temperature_2m,weathercode,precipitation",
            "timezone": "Asia/Seoul",
            "forecast_days": 1,
        }
    ).json()
    current = res["current"]
    temp = current["temperature_2m"]
    code = current["weathercode"]
    weather_map = {
        0: "☀️ 맑음", 1: "🌤️ 대체로 맑음", 2: "⛅ 구름 조금", 3: "☁️ 흐림",
        51: "🌦️ 이슬비", 61: "🌧️ 비", 71: "❄️ 눈", 80: "🌧️ 소나기",
    }
    desc = weather_map.get(code, "🌈 날씨 확인 필요")
    return desc + " " + str(temp) + "°C"

def send_kakao(token, message):
    message = message[:900]
    requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": "Bearer " + token},
        data={"template_object": json.dumps({
            "object_type": "text",
            "text": message,
            "link": {"web_url": "https://www.naver.com"}
        })}
    )

def main():
    now = datetime.now()
    days = ["월", "화", "수", "목", "금", "토", "일"]
    today_str = now.strftime("%m월 %d일 (") + days[now.weekday()] + ")"

    token = refresh_kakao_token()
    meal = get_meal()
    news = get_news()
    weather = get_weather()

    msg = "🌅 " + today_str + " 모닝 브리핑\n\n"
    msg += "🌤️ 날씨\n" + weather + "\n\n"
    msg += "📰 오늘의 뉴스\n" + news + "\n\n"
    msg += "🍱 오늘의 급식\n" + (meal if meal else "급식 정보 없음 (방학 또는 휴일)")

    send_kakao(token, msg)

if __name__ == "__main__":
    main()
