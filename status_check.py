# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, render_template, abort, jsonify
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import time
import logging
import logging.handlers
import random
import subprocess
from chans_settings import chans
import concurrent.futures
import uuid
import hashlib
import hmac

from dao import DatabaseConnector, dateformat, short_dateformat


# import karol_api as karol
karol_present = False

app = Flask(__name__)

irc_servs = OrderedDict()
running = False
sleep_minutes = 5
trk_count = 6
processes = 4
last_check = None
last_posts_check = None
log_level = logging.INFO
logger = None
db = None
checking_fred = None


def initialize():
    init_logger()
    logger.info("Inicjalizacja...")
    logger.debug("Karol: " + str(karol_present))
    try:
        start_checking()
    except Exception as e:
        logger.error("Problem przy startowaniu pętli sprawdzającej: ", e)


def chansort(chan):
    if not chan.OK:
        return -2
    if chan.users_online == "n/d" or chan.users_online == '':
        return -1
    else:
        return int(chan.users_online)


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
        h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception as e:
        logger.exception(e)
    if not h:
        h = "???????"
    return h


commit = get_commit_hash()


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

def check_single_chan(chan):
    logger.debug("Sprawdzenia " + chan.address)
    chan.parse_status()
    logger.debug(chan.status)
    if chan.OK:
        chan.check_users_online()


def check_chan_posts(chan):
    if not chan.OK:
        report_status(chan.address, chan.status_code)
        return
    db = DatabaseConnector()
    chan.check_posts_per_hour(db)
    db.insert_stats_record(chan.name, str(last_check), chan.OK, chan.users_online, chan.posts_per_hour)
    db.dispose()


def check_continously():
    global last_check, last_posts_check
    while running:
        logger.debug("Sprawdzam statusy serwisów...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            chan_results = [executor.submit(check_single_chan, c) for c in chans]
            output = [r.result() for r in chan_results]

        last_check = datetime.now()

        if last_posts_check is None or datetime.now() - last_posts_check >= timedelta(hours=1):
            logger.info("Sprawdzam posty...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                posts_results = [executor.submit(check_chan_posts, c) for c in chans]
                output = [r.result() for r in posts_results]
            last_posts_check = last_check

        logger.debug("Zakończono sprawdzanie. Idę spać na {0} minut".format(sleep_minutes))
        time.sleep(sleep_minutes * 60)


def start_checking():
    global running, checking_fred
    checking_fred = threading.Thread(target=check_continously)
    running = True
    checking_fred.start()


def stop_checking():
    global running, checking_fred
    running = False
    checking_fred.join()


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


def round_numbers(numbers, idx):
    result = []
    for n in numbers:
        if n[idx] is not None and type(n[idx]) != str:
            result.append(round(n[idx], 2))
        else:
            result.append(0)
    return result


def get_dates(request):
    """
    Zwraca krotkę (date_from, date_to) lub None
    """
    try:
        if request is not None and 'date_from' in request.form and request.form['date_from']:
            date_from = request.form['date_from']
        else:
            date_from = str(datetime.now() - timedelta(hours=12))
        if request is not None and 'date_to' in request.form and request.form['date_to']:
            date_to = request.form['date_to']
        else:
            date_to = str(datetime.now() + timedelta(hours=1))
        return (date_from, date_to)
    except Exception as ex:
        logging.exeption("Błąd przy parsowaniu daty do statystyk", ex)
        return None


def parse_dates(date_from, date_to):
    """
    Zwraca krotkę (date_from, date_to) lub None
    """
    if len(date_from) > 10:
        frmt = dateformat
    else:
        frmt = short_dateformat
    # dateformat = "%Y-%m-%d"
    try:
        inst_from = datetime.strptime(date_from, frmt)
        inst_to = datetime.strptime(date_to, frmt)
        return (inst_from, inst_to)
    except Exception as err:
        logger.exception(err)
        return None


@app.route("/stats/<chan_name>", methods=['GET', 'POST'])
def show_stats(chan_name):
    current_style = request.cookies.get('style')
    dark = current_style == 'dark'
    dates = get_dates(request)
    if dates is None:
        return "Coś zjebałeś z tymi datami stary"
    chan = list(filter(lambda x: x.name == chan_name, chans))
    view = "UUU sprawdzanko {0} {1} do {2} z {3}".format(chan_name, dates[0], dates[1], get_user_agent(request))
    logger.info(view)
    if len(chan) < 1:
        abort(404)
    if chan[0].boards is None and chan[0].users_online_url is None:
        return "Brak szczegółowych statystyk na temat '{0}'".format(chan_name)
    parsed_dates = parse_dates(*dates)
    if parsed_dates is None:
        return "Proszę sobie nie robić ziajtów"
    db = DatabaseConnector()
    date_from, date_to = parsed_dates
    try:
        stats = db.calculate_average(chan_name, date_from, date_to)
    except Exception as ex:
        logger.exception(ex)
        db.dispose()
        return "Coś poszło nie tak, prawdopodobnie nie ma danych z wybranego okresu"
    db.dispose()
    periods = list(map(lambda x: str(x[0]), stats))
    users = False
    users = round_numbers(stats, 1)
    posts = round_numbers(stats, 2)
    return render_template('chart.html', chan_name=chan_name, periods=periods, posts=posts, users=users, dark=dark)


@app.route("/styleSwitch")
def switch_style():
    current_style = request.cookies.get('style')
    redirect_to_index = redirect('/')
    response = app.make_response(redirect_to_index)
    if current_style == 'dark':
        new_style = 'rowerek'
    else:
        new_style = 'dark'
    expire_date = datetime.now() + timedelta(days=365)
    response.set_cookie('style', value=new_style, expires=expire_date)
    return response


@app.route("/")
def hello():
    current_style = request.cookies.get('style')
    dark = current_style == 'dark'
    view = "Wejście z " + get_user_agent(request)
    trk = random.choice(range(trk_count))
    logger.info(view)
    chanlist = sorted(chans, key=chansort, reverse=True)
    return render_template('index.html', chans=chanlist, last_check=last_check, trk=trk, commit_hash=commit, dark=dark)


# --- TRK Racer ---

@app.route("/racer")
def racer():
    current_style = request.cookies.get('style')
    dark = current_style == 'dark'
    view = "GRACZ {0}".format(get_user_agent(request))
    logger.info(view)
    response = app.make_response(render_template("racer.html", dark=dark))
    response.set_cookie("_tr", uuid.uuid4().hex)
    return response


@app.route("/highscores", methods=['GET', 'POST'])
def highscores():
    db = DatabaseConnector()
    scores = db.get_scores()
    db.dispose()
    return jsonify(scores)


@app.route("/setscore", methods=['POST'])
def setscore():
    try:
        tr = request.cookies.get('_tr')
        data = request.get_json(force=True)
        logger.debug(data)
        if data is None:
            return "Nic z tego stary", 400
        client_hash = data["_k"]
        score = data["score"]
        name = data["name"]
        logger.info("HIGHSCORE {0}: {1}".format(name, score))
        server_hash = hashlib.sha224("{0}mmm{1}{2}".format(tr, score, name).encode()).hexdigest()
        correct = hmac.compare_digest(client_hash, server_hash)
        if not correct:
            return "Nic z tego stary", 401
    except Exception as err:
        logger.exception(err)
        return "Nic z tego stary", 403
    try:
        db = DatabaseConnector()
        db.set_score(name, score)
    except Exception as ex:
        logger.exception(ex)
        db.dispose()
        return "Nic z tego stary", 405
    db.dispose()
    return jsonify({"success": True})


initialize()
if __name__ == "__main__":

    try:
        app.run()
    except Exception as e:
        logger.critical("Problem przy startowaniu webaplikacji: " + e)
