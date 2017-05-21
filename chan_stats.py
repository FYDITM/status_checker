import requests
from bs4 import BeautifulSoup


class ChanStats:

    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.OK = False
        self.users_online = "n/a"
        self.status = "n/a"
        self.status_code = "n/a"
        self.users_online = False
        self.users_online_url = False
        if "http://" not in self.address:
            self.address = "http://" + self.address
        self.posts_per_hour = False

    def check_status(self):
        try:
            request = requests.get(self.address, verify=False)
        except:
            return -1
        return request.status_code

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
            result += "(kod statusu: " + str(self.status_code) + ")"
        self.status = result

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
        self.selector = selector
        return self

    def check_users_online(self):
        if not self.users_online_url:
            return

        content = requests.get(self.users_online_url, verify=False).content.decode()

        if self.selector:
            # w sumie na żadnym czanie w tej chwili w ten sposób tak się nie da nic złapać
            site = BeautifulSoup(content, "html.parser")
            content = site.find_all(attrs=self.selector)[0]

        if self.eStart:
            self.users_online = content[content.index(self.eStart) + len(self.eStart):content.index(self.eStop)].strip()

        else:
            self.users_online = content
