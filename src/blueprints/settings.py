from flask import Blueprint, request, jsonify, current_app, render_template, Response
from utils.time_utils import calculate_seconds
from datetime import datetime, timedelta
import os
import pytz
import logging
import io
import requests

# Try to import cysystemd for journal reading (Linux only)
try:
    from cysystemd.reader import JournalReader, JournalOpenMode, Rule
    JOURNAL_AVAILABLE = True
except ImportError:
    JOURNAL_AVAILABLE = False
    # Define dummy classes for when cysystemd is not available
    class JournalOpenMode:
        SYSTEM = None
    class Rule:
        pass
    class JournalReader:
        def __init__(self, *args, **kwargs):
            pass


logger = logging.getLogger(__name__)
settings_bp = Blueprint("settings", __name__)

@settings_bp.route('/api/device/config', methods=['GET'])
def get_device_config():
    """Get device configuration including default location."""
    device_config = current_app.config['DEVICE_CONFIG']
    try:
        config = device_config.get_config()  # 返回整个config
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting device config: {e}")
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/settings')
def settings_page():
    device_config = current_app.config['DEVICE_CONFIG']
    timezones = sorted(pytz.all_timezones_set)
    return render_template('settings.html', device_settings=device_config.get_config(), timezones = timezones)

@settings_bp.route('/save_settings', methods=['POST'])
def save_settings():
    device_config = current_app.config['DEVICE_CONFIG']

    try:
        form_data = request.form.to_dict()

        unit, interval, time_format = form_data.get('unit'), form_data.get("interval"), form_data.get("timeFormat")
        if not unit or unit not in ["minute", "hour"]:
            return jsonify({"error": "Plugin cycle interval unit is required"}), 400
        if not interval or not interval.isnumeric():
            return jsonify({"error": "Refresh interval is required"}), 400
        if not form_data.get("timezoneName"):
            return jsonify({"error": "Time Zone is required"}), 400
        if not time_format or time_format not in ["12h", "24h"]:
            return jsonify({"error": "Time format is required"}), 400
        previous_interval_seconds = device_config.get_config("plugin_cycle_interval_seconds")
        plugin_cycle_interval_seconds = calculate_seconds(int(interval), unit)
        if plugin_cycle_interval_seconds > 86400 or plugin_cycle_interval_seconds <= 0:
            return jsonify({"error": "Plugin cycle interval must be less than 24 hours"}), 400

        settings = {
            "name": form_data.get("deviceName"),
            "orientation": form_data.get("orientation"),
            "inverted_image": form_data.get("invertImage"),
            "log_system_stats": form_data.get("logSystemStats"),
            "timezone": form_data.get("timezoneName"),
            "time_format": form_data.get("timeFormat"),
            "plugin_cycle_interval_seconds": plugin_cycle_interval_seconds,
            "image_settings": {
                "saturation": float(form_data.get("saturation", "1.0")),
                "brightness": float(form_data.get("brightness", "1.0")),
                "sharpness": float(form_data.get("sharpness", "1.0")),
                "contrast": float(form_data.get("contrast", "1.0"))
            }
        }
        device_config.update_config(settings)

        if plugin_cycle_interval_seconds != previous_interval_seconds:
            # wake the background thread up to signal interval config change
            refresh_task = current_app.config['REFRESH_TASK']
            refresh_task.signal_config_change()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    return jsonify({"success": True, "message": "Saved settings."})

@settings_bp.route('/shutdown', methods=['POST'])
def shutdown():
    data = request.get_json() or {}
    if data.get("reboot"):
        logger.info("Reboot requested")
        os.system("sudo reboot")
    else:
        logger.info("Shutdown requested")
        os.system("sudo shutdown -h now")
    return jsonify({"success": True})

@settings_bp.route('/download-logs')
def download_logs():
    try:
        buffer = io.StringIO()
        
        # Get 'hours' from query parameters, default to 2 if not provided or invalid
        hours_str = request.args.get('hours', '2')
        try:
            hours = int(hours_str)
        except ValueError:
            hours = 2
        since = datetime.now() - timedelta(hours=hours)

        if not JOURNAL_AVAILABLE:
            # Return a message when running in development mode without systemd
            buffer.write(f"Log download not available in development mode (cysystemd not installed).\n")
            buffer.write(f"Logs would normally show InkyPi service logs from the last {hours} hours.\n")
            buffer.write(f"\nTo see Flask development logs, check your terminal output.\n")
        else:
            reader = JournalReader()
            reader.open(JournalOpenMode.SYSTEM)
            reader.add_filter(Rule("_SYSTEMD_UNIT", "inkypi.service"))
            reader.seek_realtime_usec(int(since.timestamp() * 1_000_000))

            for record in reader:
                try:
                    ts = datetime.fromtimestamp(record.get_realtime_usec() / 1_000_000)
                    formatted_ts = ts.strftime("%b %d %H:%M:%S")
                except Exception:
                    formatted_ts = "??? ?? ??:??:??"

                data = record.data
                hostname = data.get("_HOSTNAME", "unknown-host")
                identifier = data.get("SYSLOG_IDENTIFIER") or data.get("_COMM", "?")
                pid = data.get("_PID", "?")
                msg = data.get("MESSAGE", "").rstrip()

                # Format the log entry similar to the journalctl default output
                buffer.write(f"{formatted_ts} {hostname} {identifier}[{pid}]: {msg}\n")

        buffer.seek(0)
        # Add date and time to the filename
        now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"inkypi_{now_str}.log"
        return Response(
            buffer.read(),
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return Response(f"Error reading logs: {e}", status=500, mimetype="text/plain")

@settings_bp.route('/api/amap/ip_location', methods=['GET'])
def get_ip_location():
    """Get geolocation based on client IP address using Amap API."""
    device_config = current_app.config['DEVICE_CONFIG']
    amap_key = device_config.load_env_key("AMAP_API_KEY")

    if not amap_key:
        return jsonify({"error": "Amap API key not configured"}), 500

    try:
        # Amap IP location API
        # https://restapi.amap.com/v3/ip?key=YOUR_KEY&ip=CLIENT_IP
        url = "https://restapi.amap.com/v3/ip"
        params = {
            "key": amap_key,
            "output": "json"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(f"Amap API request failed: {response.status_code}")
            return jsonify({"error": "Failed to get location from Amap"}), 500

        data = response.json()

        if data.get('status') != '1':
            logger.error(f"Amap API returned error: {data.get('info')}")
            return jsonify({"error": data.get('info', 'Unknown error')}), 500

        # Amap returns location as "longitude,latitude" string
        location = data.get('rectangle', '')
        if not location:
            return jsonify({"error": "No location data returned"}), 500

        # Parse location - rectangle format is "lng1,lat1;lng2,lat2"
        # We'll use the center point
        coords = location.split(';')
        if len(coords) == 2:
            lng1, lat1 = coords[0].split(',')
            lng2, lat2 = coords[1].split(',')
            longitude = (float(lng1) + float(lng2)) / 2
            latitude = (float(lat1) + float(lat2)) / 2
        else:
            return jsonify({"error": "Invalid location format"}), 500

        city = data.get('city', '')
        province = data.get('province', '')

        return jsonify({
            "success": True,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "city": city,
            "province": province,
            "adcode": data.get('adcode', '')
        })

    except Exception as e:
        logger.error(f"Error getting IP location: {e}")
        return jsonify({"error": str(e)}), 500

@settings_bp.route('/api/amap/save_default_location', methods=['POST'])
def save_default_location():
    """Save latitude and longitude as default values in device config."""
    device_config = current_app.config['DEVICE_CONFIG']

    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400

        # Validate coordinates
        try:
            lat = float(latitude)
            lng = float(longitude)
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({"error": "Invalid coordinates"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid coordinate format"}), 400

        # Store in device config as default_location
        device_config.update_config({
            "default_location": {
                "latitude": lat,
                "longitude": lng
            }
        })

        return jsonify({
            "success": True,
            "message": "Default location saved successfully",
            "latitude": lat,
            "longitude": lng
        })

    except Exception as e:
        logger.error(f"Error saving default location: {e}")
        return jsonify({"error": str(e)}), 500


