# Status Checker - czanowy sprawdzacz statusów najpopularniejszych ścieków w internecie

### Wymagania do uruchomienia:
 - Python 3.5+
 - Flask (`pip install Flask`)
 - BeautifulSoup (`pip install bs4`)

 Uruchomienienie lokalne:
 `set FLASK_APP=status_check.py`
 `flask run`

 lub na gnu/linux
 `FLASK_APP=status_check.py`
 `flask run`

### TODO:
 - Zapobieganie nienaturalnie wysokim/niskim wartościom postów na godzinę (powstają prawdopodobnie przez usuwanie i/lub przenoszenie postów)
 - Poprawki w sprawdzaniu statystyk martwych (np sis i heretyk)


### Licencja
Ten zbitek kodu jest licencjonowany na zasadach [WTFPL](http://www.wtfpl.net/)


