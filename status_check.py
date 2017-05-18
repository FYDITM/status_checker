# -*- coding: utf-8 -*-
from flask import Flask, request, render_template
from datetime import datetime
from collections import OrderedDict
import requests
import threading
import time
import logging
import logging.handlers

app = Flask(__name__)

chans = OrderedDict()
irc_servs = OrderedDict()
running = False
sleep_minutes = 5
last_check = None
log_level = logging.INFO
logger = None


def init_logger():
    global logger
    max_file_size = 52428800  # 50 MB
    log_filename = "status.log"
    logger = logging.getLogger("custom")
    logger.setLevel(log_level)
    handler = logging.handlers.RotatingFileHandler(
        log_filename, maxBytes=max_file_size, backupCount=5, encoding='utf-8')
    logger.addHandler(handler)


def log(text, level):
    logger.log(level, "[{0}]: {1}\n".format(datetime.now(), text))


def report_status(address, status_code):
    msg = "Wygląda na to, że {0} nie jeździ. Kod statusu: {1}".format(
        address, status_code)
    log(msg, logging.INFO)
    # można wysłać do Karola czy coś


def parse_status(address):
    result = ""
    status_code = check_status(address)
    if 200 <= status_code < 300:
        return "jeździ"
    else:
        report_status(address, status_code)
        result += "spadł z rowerka"
    if status_code != -1:
        result += "(kod statusu: " + str(status_code) + ")"
    return result


def check_irc_server(server):
    global irc_servs
    address = "http://" + server + ".6irc.net"
    irc_servs[server] = parse_status(address)


def check_site_status(name, site):
    global chans
    address = "http://" + site
    chans[name] = parse_status(address)


def check_status(address):
    try:
        request = requests.get(address, verify=False)
    except:
        return -1
    return request.status_code


def check_continously():
    global last_check
    while running:
        log("Sprawdzam statusy serwisów...", logging.DEBUG)
        check_site_status("kara", "karachan.org/b")
        check_site_status("vi", "pl.vichan.net")
        check_site_status("wilno", "wilchan.org")
        check_site_status("heretyk", "heretyk.org")
        check_site_status("kiwi", "kiwiszon.org/kusaba.php")
        check_site_status("sis", "sischan.xyz")
        check_site_status("lenachan", "lenachan.eu.org")
        check_site_status("żywegówno", "zywegowno.club")
        check_site_status("chanarchive", "chanarchive.pw")

        check_irc_server("polarity")
        check_irc_server("sundance")
        check_irc_server("narkotyki")
        last_check = datetime.now()
        log("Zakończono sprawdzanie. Idę spać na {0} minut".format(
            sleep_minutes), logging.DEBUG)
        time.sleep(sleep_minutes * 60)


def start_checking():
    checking_fred = threading.Thread(target=check_continously)
    global running
    running = True
    checking_fred.start()


@app.route("/")
def hello():
    ip = request.environ["REMOTE_ADDR"]
    if "X-Forwarded-For" in request.environ:
        ip = request.environ["X-Forwarded-For"]
    view = "Wejście z {ip}: {user_agent}.".format(
        ip=ip,
        user_agent=request.environ["HTTP_USER_AGENT"])
    if "HTTP_REFERER" in request.environ:
        view += " Referer:" + request.environ["HTTP_REFERER"]

    log(view, logging.INFO)
    return render_template('index.html', chans=chans, irc_servs=irc_servs, last_check=last_check)


init_logger()
log("Start aplikacji", logging.DEBUG)
if not running:
    try:
        start_checking()
    except Exception as e:
        log("Problem przy startowaniu pętli sprawdzającej: " + e, logging.ERROR)
if __name__ == "__main__":
    try:
        app.run()
    except Exception as e:
        log("Problem przy startowaniu webaplikacji: " + e, logging.ERROR)
