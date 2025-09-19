import requests
import random

# Router Configuration
ROUTER_IP = "192.168.2.1"  # Replace with your router's IP
USERNAME = "utco"  # Replace with your username
PASSWORD = "pickpock.45B"  # Replace with your password


def generate_otp():
    """Generates a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_sms(phone_number, message):
    """Sends an SMS via the router's built-in messaging API"""
    url = f"http://{ROUTER_IP}/cgi-bin/sms_send?username={USERNAME}&password={PASSWORD}&number={phone_number}&text={message}"

    try:
        response = requests.get(url)

        if response.status_code == 200 and "OK" in response.text:
            return {"success": True, "message": "SMS sent successfully!"}
        else:
            return {"success": False, "message": f"Failed to send SMS: {response.text}"}

    except requests.RequestException as e:
        return {"success": False, "message": f"Error sending SMS: {str(e)}"}


def send_otp(phone_number):
    """Generates and sends an OTP to the provided phone number"""
    otp = generate_otp()
    message = f"Your Utility Copilot OTP is {otp}. DontReply"
    return send_sms(phone_number, message)
