import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup


logger = logging.getLogger("rowerek")
timeout = 30
not_available = "n/d"


class ChanStats:

    def __init__(self, name, address, cookie=None):
        self.name = name
        self.address = address
        if "http://" not in self.address:
            self.address = "http://" + self.address
        self.boards_url = self.address
        self.notes = ""
        self.OK = False
        self.users_online = not_available
        self.status = not_available
        self.status_code = not_available
        self.users_online_url = None
        self.boards = None
        self.posts_per_hour = None
        self.cookie = cookie

    def users_online_settings(self, url, eStart=None, eStop=None, selector=None):
        """
        :param url: pełny adres, np http://karachan.org/online.php
        :param eStart: wyrażenie po którym znajduje się liczba online
        :param eStop: wyrażenie występujące po liczbie online
        :param selector: słownik atrybutów cssowych elementu, np {'id':'counter'}
        """
        if eStart and not eStop:
            raise Exception("Nie podano wyrażenia końcowego przy sprawdzaniu liczby userów online")
        self.users_online_url = url
        self.eStart = eStart
        self.eStop = eStop
        self.online_selector = selector
        return self

    def last_post_settings(self, boards, selector, url=None):
        """
        :param boards: krotka z boardami, np ('b', 'thc', 'soc')
        :param selector: słownik atrybutów cssowych elementu, np {'class':'quotePost'}
        :param url: adres przez który trzeba odwoływać się do boardów jeśli inny niż standardowy, np http://kiwiszon.org/boards/
        """
        self.boards = boards
        self.post_selector = selector
        if url is not None:
            self.boards_url = url
        return self

    def set_notes(self, notes):
        self.notes = notes
        return self

    def get_response(self, url, operation):
        try:
            response = requests.get(url, verify=False, timeout=timeout, cookies=self.cookie)
            return response
        except requests.exceptions.ConnectionError:
            logger.debug("ConnectionError przy sprawdzaniu {0} na {1}".format(operation, self.name))
        except requests.exceptions.ConnectTimeout:
            logger.debug("ConnectTimeout przy sprawdzaniu {0} na {1}".format(operation, self.name))
        except requests.exceptions.ReadTimeout:
            logger.debug("ReadTimeout przy sprawdzaniu {0} na {1}".format(operation, self.name))
        except Exception as ex:
            logger.exception("Błąd przy sprawdzaniu {0} na {1}, url: {2}".format(operation, self.name, url))

    def check_status(self):
        response = self.get_response(self.address, "statusu")
        if response and response.status_code:
            return response.status_code
        else:
            return -1

    def parse_status(self):
        result = ""
        self.status_code = self.check_status()
        if 200 <= self.status_code < 300:
            self.status = "jeździ"
            self.OK = True
            return
        else:
            result += "spadł z rowerka"
            self.OK = False
        if self.status_code != -1:
            result += " (kod statusu: " + str(self.status_code) + ")"
        self.status = result

    def check_users_online(self):
        if not self.users_online_url:
            return

        response = self.get_response(self.users_online_url, "userów online")
        if not response:
            self.users_online = not_available
            return
        content = response.content.decode()
        try:
            if self.online_selector:
                site = BeautifulSoup(content, "html.parser")
                content = site.select_one(self.online_selector)

            if self.eStart:
                self.users_online = content[content.index(self.eStart) + len(self.eStart):content.index(self.eStop)].strip()

            else:
                self.users_online = content
        except Exception as ex:
            logger.exception("Błąd przy parsowaniu liczby online na " + self.users_online_url)

    def get_current_post(self, url):
        response = self.get_response(url, "aktualnego posta")
        if not response:
            return None
        try:
            site = BeautifulSoup(response.content.decode(), 'html.parser')
            nodes = site.select(self.post_selector)
        except Exception:
            logger.exception("Błąd przy parsowaniu aktualnego posta na " + url)
        postIds = []
        if nodes is None or len(nodes) < 1:
            return None
        for node in nodes:
            try:
                postId = int(node.text)
            except:
                # na takiej megucy czasem nagłówki są puste
                continue
            if postId:
                postIds.append(postId)
        postIds.sort(reverse=True)
        lastId = postIds[0]
        return lastId

    def check_posts_per_hour(self, db):
        if not self.boards:
            return

        address = self.address
        if self.boards_url:
            address = self.boards_url

        posts_sum = 0
        for board in self.boards:
            url = "{0}/{1}".format(address, board)
            last_id = None
            current_id = None
            try:
                current_id = self.get_current_post(url)
                last_id = db.get_post_number_hour_ago(self.name, board)
            except Exception as ex:
                logger.error("Błąd przy sprawdzaniu id postów na {0}: {1}".format(url, str(ex)))
            if last_id and current_id:
                posts_sum += (current_id - last_id)
                if posts_sum < 0:
                    if self.posts_per_hour is not None and self.posts_per_hour > 0:
                        # jeśli teraz wychodzi mniej niż zero, to prawdopodobnie były usunięte jakieś posty, więc na razie dajemy ostatnią wartość
                        posts_sum = self.posts_per_hour
                    else:
                        posts_sum = 0

            db.insert_posts_record(self.name, datetime.now().timestamp(), board, current_id)
        self.posts_per_hour = posts_sum
