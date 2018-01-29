# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, abort, json
from datetime import datetime, timedelta
from collections import OrderedDict
import requests
import threading
import time
import logging, logging.handlers
import random
import re
import subprocess
from chan_stats import ChanStats

from dao import DatabaseConnector


import karol_api as karol
karol_present = True

app = Flask(__name__)

chans = []
irc_servs = OrderedDict()
running = False
sleep_minutes = 5
trk_count = 6
last_check = None
last_posts_check = None
log_level = logging.INFO
logger = None
db = None



def initialize():
    init_logger()
    logger.info("Inicjalizacja...") 
    logger.debug("Karol: " + str(karol_present))
    global chans
    tinyboard_selector = {"onclick": re.compile("citeReply*")}
    mitsuba_selector = {'class': 'quotePost'}
    meguca_selector = {'class': 'quote'}

    chans = [
        ChanStats('kara', 'karachan.org')
        .users_online_settings("http://karachan.org/online.php", "createTextNode('", "'), a.nextSibling")
        .last_post_settings(('id','4','b','z','$','c','co','a','edu','f','fa','h','wat','ku','l','med','mil','mu','oc','p','sp','tech','thc','trv','v8','vg','x','og','r','kara','g','s'), 
                            mitsuba_selector),
        ChanStats('vi', 'pl.vichan.net')
        .users_online_settings("https://pl.vichan.net/online.php", "innerHTML+='", "| Aktywne")
        .last_post_settings(('b','cp','id','int','r+oc','slav','veto','waifu','wiz','btc','c','c++','fso','h','kib','ku','lsd','psl','sci','trv','vg','a','ac','az','fr','hk','lit','mu','tv','vp','x','med','pr','pro','psy','sex','soc','sr','swag','trap','chan','meta','mit'),
            tinyboard_selector),
        ChanStats("wilno", "wilchan.org")
        .users_online_settings("https://wilchan.org/licznik.php")
        .last_post_settings(('b', 'a', 'art', 'mf', 'vg', 'porn', 'lsd', 'h', 'o', 'pol', 'text', 'int'), 
            tinyboard_selector),
        ChanStats("heretyk", "heretyk.org")
        .last_post_settings(('b','t','meta'),
            {"onclick":re.compile("return insert*")}),
        # do sprawdzenia online na kiwi potrzeba ustawionego ciasteczka z zaakceptowanym regulaminem i phpSessionId :/
        ChanStats("kiwi", "kiwiszon.org/kusaba.php"),
        ChanStats("sis", "sischan.xyz")
        .users_online_settings("http://sischan.xyz/online.php", "TextNode('", "'), a.next")
        .last_post_settings(('a', 'sis', 's', 'meta'),
            mitsuba_selector),
        ChanStats("lenachan", "lenachan.eu.org")
        .last_post_settings(('b', 'int'),
            tinyboard_selector),
        ChanStats("gówno", "gowno.club")
         # .users_online_settings("http://gowno.club/b", eStart="(", eStop=")", selector={"id": "page-title"})
        .last_post_settings(('b',), meguca_selector),

        ChanStats("korniszon", "kornichan.xyz"),

        # .last_post_settings(("b","$","a","c","ku","r4","sp","thc","trv","vg","f","fa","lit","mu","dt","hp","kib","mil","pol","x","med","s","waifu","z","fz","meta"),
        #     tinyboard_selector),
        # ChanStats("rybik", "rybik.ga"),
        # ChanStats("chanarchive", "chanarchive.pw")
    ]
    try:
        start_checking()
    except Exception as e:
        logger.error("Problem przy startowaniu pętli sprawdzającej: " + e)


def init_logger():
    global logger
    max_file_size = 52428800  # 50 MB
    log_filename = "status.log"
    logger = logging.getLogger("rowerek")
    logger.setLevel(log_level)
    handler = logging.handlers.RotatingFileHandler(
        log_filename, maxBytes=max_file_size, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter("[%(asctime)s] (%(levelname)s): %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_commit_hash():
    h = ""
    try:
        h = subprocess.check_output("git rev-parse --short HEAD").decode()
    except Exception as e:
        logger.exception(e)
    if not h:
        h = "???????"
    return h


def report_status(address, status_code):
    msg = "Wygląda na to, że {0} spadł z rowerka. ".format(address)
    if status_code != -1:
        msg += "Kod statusu {0}".format(status_code)
    logger.info(msg)
    if karol_present:
        logger.debug("Wysyłam wiadomość przez Karola...")
        if "vichan" in address:
            msg = "czaks: " + msg
        try:
            karol.send_message(msg)
        except Exception as ex:
            logger.error("Problem z wysyłaniem wiadomości przez Karola: " + str(msg))


# def check_irc_server(server):
#     global irc_servs
#     result = ""
#     address = "http://" + server + ".6irc.net"
#     try:
#         status_code = requests.get(address).status_code
#     except:
#         status_code = -1
#     if 200 <= status_code < 300:
#         irc_servs[server] = "jeździ"
#         return
#     else:
#         result += "spadł z rowerka"
#     if status_code != -1:
#         result += "(kod statusu: " + str(status_code) + ")"
#     irc_servs[server] = result


def check_continously():
    global last_check, last_posts_check

    while running:
        logger.debug("Sprawdzam statusy serwisów...")
        for chan in chans:
            logger.debug("Sprawdzenia " + chan.address)
            chan.parse_status()
            logger.debug(chan.status)
            chan.check_users_online()

        last_check = datetime.now()

        if last_posts_check is None or datetime.now() - last_posts_check >= timedelta(hours=1):
            logger.debug("Sprawdzam posty...")
            db = DatabaseConnector()
            for chan in chans:
                if not chan.OK:
                    report_status(chan.address, chan.status_code)
                    continue
                chan.check_posts_per_hour(db)
                db.insert_stats_record(chan.name, str(last_check), chan.OK, chan.users_online, chan.posts_per_hour)
            last_posts_check = last_check
            db.dispose()
        logger.debug("Zakończono sprawdzanie. Idę spać na {0} minut".format(sleep_minutes))
        time.sleep(sleep_minutes * 60)


def start_checking():
    checking_fred = threading.Thread(target=check_continously)
    global running
    running = True
    checking_fred.start()


def get_user_agent(request):
    ip = request.environ["REMOTE_ADDR"]
    if "X-Forwarded-For" in request.environ:
        ip = request.environ["X-Forwarded-For"]
    view = "{ip}: {user_agent}.".format(
        ip=ip,
        user_agent=request.environ["HTTP_USER_AGENT"])
    if "HTTP_REFERER" in request.environ:
        view += " Referer:" + request.environ["HTTP_REFERER"]
    return view


@app.route("/stats/<chan_name>", methods=['GET', 'POST'])
def show_stats(chan_name):
    date_from = None
    date_to = None
    try:
        if 'date_from' in request.form and request.form['date_from']:
            date_from = request.form['date_from']
        else:
            date_from = str(datetime.now().date())
        if 'date_to' in request.form and request.form['date_to']:
            date_to = request.form['date_to']
        else:
            date_to = str(datetime.now().date() + timedelta(days=1))
    except Exception as ex:
        logging.exeption(ex)
    chan = list(filter(lambda x: x.name == chan_name, chans))
    view = "UUU sprawdzanko {0} {1} do {2} z {3}".format(chan_name, date_from, date_to, get_user_agent(request))
    logger.info(view)
    if len(chan) < 1:
        abort(404)
    db = DatabaseConnector()
    dateformat = "%Y-%m-%d"
    try:
        inst_from = datetime.strptime(date_from, dateformat)
        inst_to = datetime.strptime(date_to, dateformat)
    except:
        return "Proszę sobie nie robić ziajtów"
    try:
        stats = db.calculate_average(chan_name, inst_from, inst_to)
    except Exception as ex:
        logger.exception(ex)
        return "Coś poszło nie tak, prawdopodobnie nie ma danych z wybranego okresu"
    periods = list(map(lambda x: str(x[0]), stats))
    users = list(map(lambda x: round(x[1], 2), stats))
    if any(x is None for x in users):
        users = False
    posts = list(map(lambda x: round(x[2], 2), stats))
    return render_template('chart.html', chan_name=chan_name, periods=periods, posts=posts, users=users)


@app.route("/")
def hello():
    view = "Wejście z " + get_user_agent(request)
    trk = random.choice(range(trk_count))
    logger.info(view)

    return render_template('index.html', chans=chans, last_check=last_check, trk=trk, commit_hash=get_commit_hash())


initialize()
if __name__ == "__main__":
    try:
        app.run()
    except Exception as e:
        logger.critical("Problem przy startowaniu webaplikacji: " + e)
