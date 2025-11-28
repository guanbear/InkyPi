from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
import os
import requests
import logging
from datetime import datetime, timezone, date, timedelta
from astral import moon
import pytz
from io import BytesIO
import math

logger = logging.getLogger(__name__)

def get_moon_phase_name(phase_age: float) -> str:
    PHASES_THRESHOLDS = [
        (1.0, "newmoon"),
        (7.0, "waxingcrescent"),
        (8.5, "firstquarter"),
        (14.0, "waxinggibbous"),
        (15.5, "fullmoon"),
        (22.0, "waninggibbous"),
        (23.5, "lastquarter"),
        (29.0, "waningcrescent"),
    ]

    for threshold, phase_name in PHASES_THRESHOLDS:
        if phase_age <= threshold:
            return phase_name
    return "newmoon"

UNITS = {
    "metric": {
        "temperature": "°C",
        "speed": "km/h"
    },
    "imperial": {
        "temperature": "°F",
        "speed": "mph"
    }
}

LABELS = {
    "zh": {
        "feels_like": "体感温度",
        "sunrise": "日出",
        "sunset": "日落",
        "wind": "风速",
        "humidity": "湿度",
        "pressure": "气压",
        "uv_index": "紫外线",
        "visibility": "能见度",
        "air_quality": "空气质量",
        "last_refresh": "最后更新",
        "weather_alert": "天气预警"
    },
    "en": {
        "feels_like": "Feels Like",
        "sunrise": "Sunrise",
        "sunset": "Sunset",
        "wind": "Wind",
        "humidity": "Humidity",
        "pressure": "Pressure",
        "uv_index": "UV Index",
        "visibility": "Visibility",
        "air_quality": "Air Quality",
        "last_refresh": "Last refresh",
        "weather_alert": "Weather Alert"
    }
}

QWEATHER_ICON_MAP = {
    "100": "01d",
    "101": "02d",
    "102": "02d",
    "103": "03d",
    "104": "04d",
    "150": "02d",
    "151": "02d",
    "152": "02d",
    "153": "03d",
    "154": "04d",
    "300": "09d",
    "301": "09d",
    "302": "10d",
    "303": "11d",
    "304": "11d",
    "305": "10d",
    "306": "10d",
    "307": "10d",
    "308": "10d",
    "309": "09d",
    "310": "10d",
    "311": "10d",
    "312": "10d",
    "313": "10d",
    "314": "09d",
    "315": "10d",
    "316": "10d",
    "317": "10d",
    "318": "10d",
    "350": "09d",
    "351": "09d",
    "399": "10d",
    "400": "13d",
    "401": "13d",
    "402": "13d",
    "403": "13d",
    "404": "13d",
    "405": "13d",
    "406": "13d",
    "407": "13d",
    "408": "13d",
    "409": "13d",
    "410": "13d",
    "456": "13d",
    "457": "13d",
    "499": "13d",
    "500": "50d",
    "501": "50d",
    "502": "50d",
    "503": "50d",
    "504": "50d",
    "507": "50d",
    "508": "50d",
    "509": "50d",
    "510": "50d",
    "511": "50d",
    "512": "50d",
    "513": "50d",
    "514": "50d",
    "515": "50d",
    "800": "01d",
    "801": "02d",
    "802": "03d",
    "803": "04d",
    "804": "04d",
    "805": "04d",
    "806": "04d",
    "807": "04d"
}

class QWeather(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['api_key'] = {
            "required": True,
            "service": "QWeather (和风天气)",
            "expected_key": "QWEATHER_API_KEY"
        }
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):
        lat = settings.get('latitude')
        long = settings.get('longitude')
        if not lat or not long:
            raise RuntimeError("Latitude and Longitude are required.")

        units = settings.get('units', 'metric')
        if units not in ['metric', 'imperial']:
            raise RuntimeError("Units must be metric or imperial.")

        language = settings.get('language', 'zh')
        if language not in ['zh', 'en']:
            language = 'zh'

        theme_mode = settings.get('themeMode', 'light')
        if theme_mode not in ['light', 'dark', 'auto']:
            theme_mode = 'light'

        display_style = settings.get('displayStyle', 'default')
        if display_style not in ['default', 'nothing', 'eink']:
            display_style = 'default'

        api_key = device_config.load_env_key("QWEATHER_API_KEY")
        if not api_key:
            raise RuntimeError("QWeather API Key not configured.")

        host = settings.get('qweatherHost') or device_config.load_env_key("QWEATHER_HOST") or 'https://devapi.qweather.com'
        title = settings.get('customTitle', '')

        mock_alert_headline = settings.get('mockAlertHeadline', '')
        mock_alert_severity = settings.get('mockAlertSeverity', '')

        if mock_alert_headline and not mock_alert_severity:
            mock_alert_severity = 'moderate'
            logger.warning(f"Mock alert headline provided without severity, defaulting to 'moderate'")

        timezone = device_config.get_config("timezone", default="Asia/Shanghai")
        time_format = device_config.get_config("time_format", default="24h")
        tz = pytz.timezone(timezone)

        try:
            location_id = self.get_location_id(host, api_key, lat, long)

            weather_data = self.get_weather_data(host, api_key, location_id, units)
            daily_forecast = self.get_daily_forecast(host, api_key, location_id, units)
            minutely_forecast = self.get_minutely_forecast(host, api_key, location_id)
            hourly_forecast = self.get_hourly_forecast(host, api_key, location_id, units)
            air_quality = self.get_air_quality(host, api_key, location_id)
            weather_alerts = self.get_weather_alerts(host, api_key, lat, long)

            if mock_alert_headline:
                logger.info(f"Using mock weather alert: {mock_alert_headline}, severity: {mock_alert_severity}")
                weather_alerts = self.create_mock_alert(mock_alert_headline, '', mock_alert_severity)
                logger.info(f"Mock weather alerts created: {weather_alerts}")

            if not title:
                # Try to get location name from GeoAPI
                location_name = self.get_location_name(host, api_key, lat, long)
                if location_name:
                    title = location_name
                else:
                    # Fallback to formatted coordinates (2 decimal places)
                    title = f"{float(lat):.2f}, {float(long):.2f}"
                    logger.warning(f"Could not get location name, using coordinates: {title}")

            template_params, sunrise_dt, sunset_dt = self.parse_weather_data(
                weather_data,
                daily_forecast,
                minutely_forecast,
                hourly_forecast,
                air_quality,
                weather_alerts,
                tz,
                units,
                time_format,
                language,
                display_style
            )
            template_params['title'] = title
            template_params['labels'] = LABELS[language]

            is_dark_mode = self.determine_theme(theme_mode, sunrise_dt, sunset_dt, tz)
            template_params['dark_mode'] = is_dark_mode
            template_params['display_style'] = display_style

        except Exception as e:
            logger.error(f"QWeather request failed: {str(e)}")
            raise RuntimeError(f"QWeather request failure: {str(e)}")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        template_params["plugin_settings"] = settings

        now = datetime.now(tz)
        if time_format == "24h":
            last_refresh_time = now.strftime("%Y-%m-%d %H:%M")
        else:
            last_refresh_time = now.strftime("%Y-%m-%d %I:%M %p")
        template_params["last_refresh_time"] = last_refresh_time
        template_params["language"] = language

        image = self.render_image(dimensions, "qweather.html", "qweather.css", template_params)

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
        return image

    def get_location_id(self, host, api_key, lat, long):
        return f"{long},{lat}"

    def get_location_name(self, host, api_key, lat, long):
        """Get location name from coordinates using QWeather GeoAPI"""
        # Format coordinates to 2 decimal places as required by QWeather API
        lat_formatted = f"{float(lat):.2f}"
        long_formatted = f"{float(long):.2f}"

        # Check if using custom host
        is_custom_host = 'qweatherapi.com' in host and 'devapi' not in host and 'api.qweather.com' not in host

        if is_custom_host:
            # Custom host uses /geo/ prefix with key parameter
            url = f"{host}/geo/v2/city/lookup"
        else:
            # Standard host
            url = f"{host}/v2/city/lookup"

        params = {
            "location": f"{long_formatted},{lat_formatted}",
            "key": api_key
        }
        logger.info(f"Requesting location name from: {url} with location: {params['location']}")

        try:
            response = requests.get(url, params=params, timeout=10)
            logger.info(f"Location API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Location API response: {data}")
                if data.get('code') == '200' and data.get('location') and len(data['location']) > 0:
                    loc = data['location'][0]
                    # Build location name from name, adm2, adm1
                    # Example: "东城 北京 北京市" or "Beijing Beijing"
                    parts = []
                    name = loc.get('name', '')
                    adm2 = loc.get('adm2', '')
                    adm1 = loc.get('adm1', '')

                    # Add unique parts (avoid duplication)
                    if name and name not in parts:
                        parts.append(name)
                    if adm2 and adm2 not in parts and adm2 != name:
                        parts.append(adm2)
                    if adm1 and adm1 not in parts and adm1 != adm2:
                        parts.append(adm1)

                    location_name = ' '.join(parts) if parts else loc.get('country', '')
                    logger.info(f"Found location name: {location_name}")
                    return location_name
                else:
                    logger.warning(f"Location API returned code: {data.get('code')}, locations: {data.get('location')}")
        except Exception as e:
            logger.error(f"Failed to get location name: {e}")

        return ""

    def get_weather_data(self, host, api_key, location_id, units):
        url = f"{host}/v7/weather/now"
        params = {
            "location": location_id,
            "key": api_key,
            "unit": "m" if units == "metric" else "i"
        }
        logger.info(f"Requesting weather data from: {url} with params: {params}")
        response = requests.get(url, params=params)
        logger.info(f"Response status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Failed to retrieve weather data. Status: {response.status_code}, Content: {response.content}")
            raise RuntimeError(f"Failed to retrieve weather data. Status: {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}, Content: {response.text}")
            raise RuntimeError("Failed to parse weather data.")

        if data.get('code') != '200':
            logger.error(f"Invalid weather response: {data}")
            raise RuntimeError("Failed to get valid weather data.")

        return data['now']

    def get_daily_forecast(self, host, api_key, location_id, units):
        url = f"{host}/v7/weather/7d"
        params = {
            "location": location_id,
            "key": api_key,
            "unit": "m" if units == "metric" else "i"
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"Failed to retrieve daily forecast. Status: {response.status_code}, Content: {response.content}")
            raise RuntimeError("Failed to retrieve daily forecast.")

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}, Content: {response.text}")
            raise RuntimeError("Failed to parse forecast data.")

        if data.get('code') != '200':
            logger.error(f"Invalid forecast response: {data}")
            raise RuntimeError("Failed to get valid forecast data.")

        return data['daily']

    def get_hourly_forecast(self, host, api_key, location_id, units):
        url = f"{host}/v7/weather/24h"
        params = {
            "location": location_id,
            "key": api_key,
            "unit": "m" if units == "metric" else "i"
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"Failed to retrieve hourly forecast. Status: {response.status_code}, Content: {response.content}")
            raise RuntimeError("Failed to retrieve hourly forecast.")

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}, Content: {response.text}")
            raise RuntimeError("Failed to parse hourly forecast data.")

        if data.get('code') != '200':
            logger.error(f"Invalid hourly forecast response: {data}")
            raise RuntimeError("Failed to get valid hourly forecast data.")

        return data['hourly']

    def get_minutely_forecast(self, host, api_key, location_id):
        url = f"{host}/v7/minutely/5m"
        params = {
            "location": location_id,
            "key": api_key
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.warning(f"Failed to retrieve minutely forecast. Status: {response.status_code}, falling back to hourly only")
            return []

        try:
            data = response.json()
        except Exception as e:
            logger.warning(f"Failed to parse minutely JSON response: {e}, falling back to hourly only")
            return []

        if data.get('code') != '200':
            logger.warning(f"Invalid minutely forecast response: {data}, falling back to hourly only")
            return []

        return data.get('minutely', [])

    def get_air_quality(self, host, api_key, location_id):
        long, lat = location_id.split(',')
        url = f"{host}/airquality/v1/current/{lat}/{long}"
        params = {
            "key": api_key
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"Failed to get air quality data: {response.content}")
            return {}

        try:
            data = response.json()
            if data.get('indexes') and len(data['indexes']) > 0:
                cn_mee = data['indexes'][0]
                return {
                    'aqi': cn_mee.get('aqi', 'N/A'),
                    'category': cn_mee.get('category', '')
                }
        except Exception as e:
            logger.error(f"Failed to parse air quality response: {e}")

        return {}

    def get_weather_alerts(self, host, api_key, lat, long):
        url = f"{host}/weatheralert/v1/current/{lat}/{long}"
        params = {
            "key": api_key
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"Failed to get weather alerts: {response.content}")
            return []

        try:
            data = response.json()
            alerts = data.get('alerts', [])
            if alerts:
                logger.info(f"Found {len(alerts)} weather alert(s)")
            return alerts
        except Exception as e:
            logger.error(f"Failed to parse weather alerts response: {e}")

        return []

    def create_mock_alert(self, headline, description, severity):
        return [{
            'headline': headline,
            'description': description,
            'severity': severity,
            'eventType': {'name': headline},
            'issuedTime': datetime.now().isoformat(),
            'expireTime': (datetime.now() + timedelta(hours=24)).isoformat()
        }]

    def parse_weather_data(self, weather_data, daily_forecast, minutely_forecast, hourly_forecast, air_quality, weather_alerts, tz, units, time_format, language="zh", display_style="default"):
        current_icon = self.map_qweather_icon(weather_data.get('icon', '100'), display_style)
        current_temp = float(weather_data.get('temp', 0))
        feels_like = float(weather_data.get('feelsLike', current_temp))

        if language == "zh":
            now = datetime.now(tz)
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
            current_date = f"{weekdays[now.weekday()]}, {months[now.month - 1]} {now.day}日"
        else:
            current_date = datetime.now(tz).strftime("%A, %B %d")

        data = {
            "current_date": current_date,
            "current_day_icon": self.get_plugin_dir(f'icons/{current_icon}.png' if display_style != "eink" else f'icons/{current_icon}'),
            "current_temperature": str(round(current_temp)),
            "feels_like": str(round(feels_like)),
            "temperature_unit": UNITS[units]["temperature"],
            "units": units,
            "time_format": time_format
        }

        data['forecast'] = self.parse_forecast(daily_forecast, tz, language, display_style)
        data['data_points'], sunrise_dt, sunset_dt = self.parse_data_points(weather_data, daily_forecast[0] if daily_forecast else {}, air_quality, tz, units, time_format, language)
        data['hourly_forecast'] = self.merge_minutely_and_hourly(minutely_forecast, hourly_forecast, tz, time_format, units)
        data['weather_alerts'] = self.parse_weather_alerts(weather_alerts, language)

        if data['forecast']:
            forecast_temps = []
            for day in data['forecast']:
                forecast_temps.append(day['high'])
                forecast_temps.append(day['low'])
            data['forecast_temp_max'] = max(forecast_temps) if forecast_temps else 0
            data['forecast_temp_min'] = min(forecast_temps) if forecast_temps else 0
        else:
            data['forecast_temp_max'] = 0
            data['forecast_temp_min'] = 0

        return data, sunrise_dt, sunset_dt

    def map_qweather_icon(self, qweather_icon, display_style="default"):
        """
        Map QWeather icon codes to appropriate file paths based on display style.
        
        Args:
            qweather_icon: QWeather API icon code (e.g., "100", "101")
            display_style: Display style ("default", "nothing", "eink")
            
        Returns:
            Icon file path relative to plugin directory
        """
        # For eink style, use QWeather official SVG icons directly
        if display_style == "eink":
            # QWeather icon codes are used as-is for SVG files
            return f"eink/{qweather_icon}.svg"
        
        # For nothing style, map to pixel icons
        if display_style == "nothing":
            # Map to OpenWeather-style codes first
            base_icon = QWEATHER_ICON_MAP.get(str(qweather_icon), "01d")
            pixel_icon_map = {
                "01d": "sun",     # 晴天 -> 太阳
                "02d": "k0",      # 少云 -> 太阳+云
                "03d": "Pf",      # 多云 -> 云
                "04d": "Hx",      # 阴天 -> 厚云
                "09d": "uu",      # 大雨 -> 云+大雨
                "10d": "xc",      # 雨 -> 云+雨
                "11d": "gk",      # 雷暴 -> 云+闪电
                "13d": "nt",      # 雪 -> 云+雪
                "50d": "p8"       # 雾/霾 -> 雾
            }
            pixel_icon = pixel_icon_map.get(base_icon, "sun")
            return f"pixel/{pixel_icon}"
        
        # Default style uses OpenWeather-style mapping
        return QWEATHER_ICON_MAP.get(str(qweather_icon), "01d")

    def parse_forecast(self, daily_forecast, tz, language="zh", display_style="default"):
        forecast = []
        today = datetime.now(tz).date()

        for idx, day in enumerate(daily_forecast):
            weather_icon = self.map_qweather_icon(day.get('iconDay', '100'), display_style)
            weather_icon_path = self.get_plugin_dir(f"icons/{weather_icon}.png" if display_style != "eink" else f"icons/{weather_icon}")

            dt = datetime.fromisoformat(day['fxDate']).replace(tzinfo=tz)

            if dt.date() == today:
                day_label = "今天" if language == "zh" else "Today"
            elif language == "zh":
                weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                day_label = weekdays[dt.weekday()]
            else:
                day_label = dt.strftime("%a")

            target_date = dt.date()
            try:
                phase_age = moon.phase(target_date)
                phase_name = get_moon_phase_name(phase_age)
                LUNAR_CYCLE_DAYS = 29.530588853
                phase_fraction = phase_age / LUNAR_CYCLE_DAYS
                illum_pct = (1 - math.cos(2 * math.pi * phase_fraction)) / 2 * 100
            except Exception as e:
                logger.error(f"Error calculating moon phase for {target_date}: {e}")
                illum_pct = 0
                phase_name = "newmoon"

            moon_icon_path = self.get_plugin_dir(f"icons/{phase_name}.png" if display_style != "eink" else f"icons/{phase_name}")

            forecast.append({
                "day": day_label,
                "high": int(float(day.get('tempMax', 0))),
                "low": int(float(day.get('tempMin', 0))),
                "icon": weather_icon_path,
                "moon_phase_pct": f"{illum_pct:.0f}",
                "moon_phase_icon": moon_icon_path,
            })

        return forecast

    def parse_hourly(self, hourly_forecast, tz, time_format, units):
        hourly = []
        current_time = datetime.now(tz)

        for hour in hourly_forecast[:24]:
            dt = datetime.fromisoformat(hour['fxTime']).replace(tzinfo=tz)

            if dt < current_time:
                continue

            precip_prob = float(hour.get('pop', 0)) / 100.0
            precip_amount = float(hour.get('precip', 0))

            if units == "imperial":
                precip_amount = precip_amount / 25.4

            hour_forecast = {
                "time": self.format_time(dt, time_format, hour_only=True),
                "temperature": int(float(hour.get('temp', 0))),
                "precipitation": precip_prob,
                "rain": round(precip_amount, 2)
            }
            hourly.append(hour_forecast)

            if len(hourly) >= 24:
                break

        return hourly

    def merge_minutely_and_hourly(self, minutely_forecast, hourly_forecast, tz, time_format, units):
        merged = []
        current_time = datetime.now(tz)
        two_hours_later = current_time + timedelta(hours=2)

        if minutely_forecast:
            logger.info(f"Using {len(minutely_forecast)} minutely forecast points for first 2 hours")
            minutely_temps = {}

            for minute_data in minutely_forecast:
                dt = datetime.fromisoformat(minute_data['fxTime']).replace(tzinfo=tz)

                if dt < current_time:
                    continue

                if dt > two_hours_later:
                    break

                hour_key = dt.replace(minute=0, second=0, microsecond=0)
                if hour_key not in minutely_temps:
                    minutely_temps[hour_key] = []

                precip_amount = float(minute_data.get('precip', 0))
                if units == "imperial":
                    precip_amount = precip_amount / 25.4

                minutely_temps[hour_key].append({
                    'precip': precip_amount,
                    'dt': dt
                })

            hourly_data = self.parse_hourly(hourly_forecast, tz, time_format, units)

            for hour_time in sorted(minutely_temps.keys()):
                if hour_time >= two_hours_later:
                    break

                temps_in_hour = minutely_temps[hour_time]
                if not temps_in_hour:
                    continue

                total_precip = sum(item['precip'] for item in temps_in_hour)

                matching_hourly = next((h for h in hourly_data if h['time'] == self.format_time(hour_time, time_format, hour_only=True)), None)
                temp = matching_hourly['temperature'] if matching_hourly else None
                precip_prob = matching_hourly['precipitation'] if matching_hourly else 0.0

                if temp is None and hourly_data:
                    temp = hourly_data[0]['temperature']

                if total_precip > 0 and precip_prob == 0:
                    if total_precip >= 2.5:
                        precip_prob = 0.9
                    elif total_precip >= 1.0:
                        precip_prob = 0.7
                    elif total_precip >= 0.1:
                        precip_prob = 0.5
                    else:
                        precip_prob = 0.3

                merged.append({
                    "time": self.format_time(hour_time, time_format, hour_only=True),
                    "temperature": temp,
                    "precipitation": precip_prob,
                    "rain": round(total_precip, 2)
                })

        hourly_parsed = self.parse_hourly(hourly_forecast, tz, time_format, units)
        for hour_data in hourly_parsed:
            hour_dt_str = hour_data['time']

            is_within_2h = False
            for existing in merged:
                if existing['time'] == hour_dt_str:
                    is_within_2h = True
                    break

            if not is_within_2h:
                merged.append(hour_data)

            if len(merged) >= 24:
                break

        logger.info(f"Merged forecast: {len(merged)} data points")
        return merged[:24]

    def parse_data_points(self, current_weather, today_forecast, air_quality, tz, units, time_format, language="zh"):
        data_points = []
        sunrise_dt = None
        sunset_dt = None

        sunrise_str = today_forecast.get('sunrise')
        if sunrise_str:
            sunrise_dt = datetime.strptime(sunrise_str, "%H:%M").replace(
                year=datetime.now(tz).year,
                month=datetime.now(tz).month,
                day=datetime.now(tz).day,
                tzinfo=tz
            )
            data_points.append({
                "label": LABELS[language]["sunrise"],
                "measurement": self.format_time(sunrise_dt, time_format, include_am_pm=False),
                "unit": "" if time_format == "24h" else sunrise_dt.strftime('%p'),
                "icon": self.get_plugin_dir('icons/sunrise.png')
            })

        sunset_str = today_forecast.get('sunset')
        if sunset_str:
            sunset_dt = datetime.strptime(sunset_str, "%H:%M").replace(
                year=datetime.now(tz).year,
                month=datetime.now(tz).month,
                day=datetime.now(tz).day,
                tzinfo=tz
            )
            data_points.append({
                "label": LABELS[language]["sunset"],
                "measurement": self.format_time(sunset_dt, time_format, include_am_pm=False),
                "unit": "" if time_format == "24h" else sunset_dt.strftime('%p'),
                "icon": self.get_plugin_dir('icons/sunset.png')
            })

        wind_speed = current_weather.get('windSpeed', '0')
        data_points.append({
            "label": LABELS[language]["wind"],
            "measurement": wind_speed,
            "unit": UNITS[units]["speed"],
            "icon": self.get_plugin_dir('icons/wind.png')
        })

        humidity = current_weather.get('humidity', '0')
        data_points.append({
            "label": LABELS[language]["humidity"],
            "measurement": humidity,
            "unit": '%',
            "icon": self.get_plugin_dir('icons/humidity.png')
        })

        pressure = current_weather.get('pressure', '0')
        data_points.append({
            "label": LABELS[language]["pressure"],
            "measurement": pressure,
            "unit": 'hPa',
            "icon": self.get_plugin_dir('icons/pressure.png')
        })

        uv_index = today_forecast.get('uvIndex', '0')
        data_points.append({
            "label": LABELS[language]["uv_index"],
            "measurement": uv_index,
            "unit": '',
            "icon": self.get_plugin_dir('icons/uvi.png')
        })

        visibility = float(current_weather.get('vis', '10'))
        visibility_str = f">{visibility}" if visibility >= 10 else visibility
        data_points.append({
            "label": LABELS[language]["visibility"],
            "measurement": visibility_str,
            "unit": 'km',
            "icon": self.get_plugin_dir('icons/visibility.png')
        })

        if air_quality:
            aqi = air_quality.get('aqi', 'N/A')
            aqi_category = air_quality.get('category', '')
            data_points.append({
                "label": LABELS[language]["air_quality"],
                "measurement": aqi,
                "unit": aqi_category,
                "icon": self.get_plugin_dir('icons/aqi.png')
            })

        return data_points, sunrise_dt, sunset_dt

    def format_time(self, dt, time_format, hour_only=False, include_am_pm=True):
        if time_format == "24h":
            return dt.strftime("%H:00" if hour_only else "%H:%M")

        if include_am_pm:
            fmt = "%-I %p" if hour_only else "%-I:%M %p"
        else:
            fmt = "%-I" if hour_only else "%-I:%M"

        return dt.strftime(fmt).lstrip("0")

    def determine_theme(self, theme_mode, sunrise_dt, sunset_dt, tz):
        if theme_mode == "light":
            return False
        elif theme_mode == "dark":
            return True
        elif theme_mode == "auto":
            if sunrise_dt and sunset_dt:
                now = datetime.now(tz)
                return now < sunrise_dt or now >= sunset_dt
            return False
        return False

    def parse_weather_alerts(self, alerts, language="zh"):
        logger.info(f"Parsing weather alerts: {len(alerts) if alerts else 0} alert(s)")
        if not alerts:
            logger.info("No weather alerts to parse")
            return []

        severity_colors = {
            "extreme": {"bg": "#8B0000", "text": "#FFFFFF"},
            "severe": {"bg": "#FF4500", "text": "#FFFFFF"},
            "moderate": {"bg": "#FFA500", "text": "#000000"},
            "minor": {"bg": "#FFD700", "text": "#000000"}
        }

        parsed_alerts = []
        for alert in alerts[:3]:
            severity = alert.get('severity', 'minor')
            colors = severity_colors.get(severity, severity_colors['minor'])

            event_name = alert.get('eventType', {}).get('name', '')
            headline = alert.get('headline', event_name)
            description = alert.get('description', '')

            if language == "en" and not headline:
                headline = alert.get('eventType', {}).get('code', 'Weather Alert')

            parsed_alerts.append({
                'headline': headline,
                'description': description[:200] if description else '',
                'severity': severity,
                'bg_color': colors['bg'],
                'text_color': colors['text'],
                'issued_time': alert.get('issuedTime', ''),
                'expire_time': alert.get('expireTime', '')
            })

        logger.info(f"Parsed {len(parsed_alerts)} weather alert(s): {parsed_alerts}")
        return parsed_alerts
