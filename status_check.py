# -*- coding: utf-8 -*-
from flask import Flask, request, render_template
from datetime import datetime
from collections import OrderedDict
import requests
import threading
import time
import logging
import logging.handlers
import random
from chan_stats import ChanStats
from lxml import html

# karol_present = False
# try:
#     import karol_api as karol
#     karol_present = True
# except:
#     karol_present = False

app = Flask(__name__)

chans = []
irc_servs = OrderedDict()
running = False
sleep_minutes = 5
trk_count = 4
last_check = None
log_level = logging.INFO
logger = None


def initialize():
    init_logger()
    log("Inicjalizacja...", logging.DEBUG)
    global chans
    chans = [
        ChanStats('kara', 'karachan.org/*/')
        .users_online_settings("http://karachan.org/online.php", "createTextNode('", "'), a.nextSibling"),
        ChanStats('vi', 'pl.vichan.net/*/')
        .users_online_settings("https://pl.vichan.net/online.php", "innerHTML+='", "| Aktywne"),
        ChanStats("wilno", "wilchan.org")
        .users_online_settings("https://wilchan.org/licznik.php"),
        ChanStats("heretyk", "heretyk.org"),
        # do sprawdzenia online potrzeba ustawionego ciasteczka z zaakceptowanym regulaminem :/
        ChanStats("kiwi", "kiwiszon.org/kusaba.php"),
        ChanStats("sis", "sischan.xyz")
        .users_online_settings("http://sischan.xyz/online.php", "TextNode('", "'), a.next"),
        ChanStats("lenachan", "lenachan.eu.org"),
        ChanStats("żywegówno", "zywegowno.club"),
        ChanStats("rybik", "rybik.ga"),
        ChanStats("chanarchive", "chanarchive.pw")
    ]
    
    chans[1].posts_per_hour = True
    
    try:
        start_checking()
    except Exception as e:
        log("Problem przy startowaniu pętli sprawdzającej: " + e, logging.ERROR)


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
    msg = "Wygląda na to, że {0} spadł z rowerka. ".format(address)
    if status_code != -1:
        msg += "Kod statusu {0}".format(status_code)
    log(msg, logging.INFO)
    # if karol_present:
    #     if "vichan" in address:
    #         msg = "czaks: " + msg
    #     karol.send_message(msg)


def check_irc_server(server):
    global irc_servs
    result = ""
    address = "http://" + server + ".6irc.net"
    try:
        status_code = requests.get(address).status_code
    except:
        status_code = -1
    if 200 <= status_code < 300:
        irc_servs[server] = "jeździ"
        return
    else:
        result += "spadł z rowerka"
    if status_code != -1:
        result += "(kod statusu: " + str(status_code) + ")"
    irc_servs[server] = result


def check_continously():
    global last_check
    while running:
        log("Sprawdzam statusy serwisów...", logging.DEBUG)
        for chan in chans:
            chan.parse_status()
            chan.check_users_online()

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


def to_seconds(t):
    seconds = time.mktime(t.timetuple())
    return seconds

def posts_lasthour_vi(time_diff=-7200):
    page = requests.get('http://pl.vichan.net/*/')
    tree = html.fromstring(page.content)

    times = tree.xpath('//time/@datetime')

    times_seconds = [time.mktime(datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').timetuple())
                     for t in times]

    times_seconds.sort()
    post_count = len(times_seconds)

    now_seconds = to_seconds(datetime.now())
    hour_ago = now_seconds - 3600
    fivemin_ago = now_seconds - (60*5)


    # powiedzmy jakbys zapostowal teraz
    # - 7200 bo strefa czasowa, nie znam sie 
    posts = 0
    for t in times_seconds[:-1]:
        if t > hour_ago + time_diff:
            posts += 1

    return posts

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
    trk = random.choice(range(trk_count))
    log(view, logging.INFO)

    posts_lasthour_vi = posts_lasthour_vi()

    return render_template('index.html', chans=chans, irc_servs=irc_servs, last_check=last_check, trk=trk, post_count=posts_lasthour_vi)


initialize()
if __name__ == "__main__":
    try:
        app.run()
    except Exception as e:
        log("Problem przy startowaniu webaplikacji: " + e, logging.ERROR)
