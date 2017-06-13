import requests


karol_url = "http://127.0.0.1:5001"


def send_message(message):
    url = karol_url + "/message"
    response = requests.post(url, data={'message': message})
