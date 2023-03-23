import requests
from datetime import datetime

from django.utils import timezone
import pytz

def get_user_agent(request):
    return request.headers.get("user-agent")

def get_ip_location(request):
    response = requests.get('http://ipinfo.io/json').json()
    data = {
        "ip": response.get("ip"),
        "location": str(response.get("city")) + str(response.get("region") + str(response.get("country"))),
        "user_agent": get_user_agent(request)
    }
    return data

def date_from_str(
    date_str,
    date_str_format='%Y-%m-%d',
    max_time=False
):
    dt = datetime.strptime(date_str, date_str_format)

    if max_time:
        dt = datetime.combine(dt.date(), datetime.max.time())

    dt = pytz.timezone(timezone.get_current_timezone_name()).localize(dt)
    return dt.astimezone(timezone.get_current_timezone())