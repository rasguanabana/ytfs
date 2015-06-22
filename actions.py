"""
Moduł odpowiedzialny za wyszukiwanie filmów w serwisach internetowych. Na chwilę obecną wspierany jest tylko YouTube.
"""

import os
import requests

from stor import YTStor

from copy import copy, deepcopy
from collections import OrderedDict

class YTActions():

    """
    Klasa pozwalająca na realizowanie operacji wyszukiwania filmów w serwisie YouTube oraz przechowująca informacje o
    wynikach wyszukiwania.

    Attributes
    ----------
    avail_files : OrderedDict
        Zawiera krotki następującej postaci:

        avail_files = {
                        "token": (adj_tokens, files),
                        ...
                    }
                                                                        
        adj_tokens to sąsiednie tokeny, files to pliki danego wyszukiwania
        (tak jak poniżej).
    visible_files : dict
        Bieżące wyniki wyszukiwania. Kluczem jest nazwa filmu, a wartością obiekt YTStor dla filmu.
    adj_tokens : dict
        Słownik tokenów sąsiednich stron wyszukiwania. Pod False znajduje się poprzednia strona, pod True - następna.
        Inne klucze nie są dozwolone.
    vf_iter : obj
        Tu klasa przechowuje iterator pozwalający na listowanie bieżącej zawartości katalogu. Używane przez __iter__
        i __next__.

    Parameters
    ----------
    search_query : str
        Fraza, wg której wyszukiwane są filmy.
    max_results : int, optional
        Ilość wyszukiwań na "stronę".
    """

    avail_files = OrderedDict()
    visible_files = None
    adj_tokens = {False: None, True: None}

    vf_iter = None

    def __init__(self, search_query, max_results = 10):

        if not isinstance(search_query, str):
            raise ValueError("Expected str for 1st parameter (search_query).")
        if not isinstance(max_results, int):
            raise ValueError("Expected int for 2nd parameter (max_results).")

        self.search_query = search_query
        self.max_results = max_results

    def __search(self, pt=None):

        """
        Metoda odpowiedzialna za wyszukiwanie w API YouTube.

        Parameters
        ----------
        pt : str
            Token strony z wynikami wyszukiwania. Jeśli None, to pobierana jest pierwsza strona.

        Returns
        -------
        results : dict
            Sparsowany json zwrócony z API YouTube.
        """

        api_fixed_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&fields=items(id%2Ckind%2Csnippet)%2CnextPageToken%2CprevPageToken"
        api_key = "AIzaSyCPOg5HQfHayQH6mRu4m2PMGc3eHd5lllg"

        url = "{0}&key={1}&maxResults={2}&q={3}&pageToken=".format(api_fixed_url, api_key, self.max_results, self.search_query)

        try:
            url += pt
        except TypeError:
            pass

        return requests.get(url).json() #FIXME? trochę gołe, a coś może pójść nie tak...

    def __iter__(self):

        """
        Stwórz iterator. Metoda umożliwia w prosty sposób zwrócić generator zawierający nazwy plików. Faktycznym
        generatorem jest self.vf_iter, obiekt YTActions (użyty jako iterator) stanowi do niego nakładkę.

        Returns
        -------
        self : YTActions
            Obiekt, potraktowany funkcją iter(), zwraca sam siebie. 
        """

        ctrl = []

        if self.adj_tokens[False] is not None:
            ctrl += [ " prev" ]
        if self.adj_tokens[True] is not None:
            ctrl += [ " next" ]

        self.vf_iter = iter(ctrl + [e + ".mp4" for e in self.visible_files])

        return self

    def __next__(self):

        """
        Obsługa next(). Zwróć następną nazwę pliku.

        Returns
        -------
        file_name : str
            Następna nazwa pliku z self.vf_iter.
        """

        return next(self.vf_iter)

    def __getitem__(self, key):

        """
        Odczytuj elementy z obiektu YTActions za pomocą klucza `key`. Metoda pozwala na używanie obiektu w podobny
        sposób jak słownika.

        Parameters
        ----------
        key : str
            Klucz (np. YTActions['Rick Astley - Never Gonna Give You Up.mp4']).

        Returns
        -------
        YTStor
            Obiekt YTStor skojarzony z nazwą `key`.
        """

        return self.visible_files[ os.path.splitext(key)[0] ] #pozbywamy się rozszerzenia, btw.

    def __in__(self, arg):

        """
        Sprawdź, czy film o nazwie `arg` znajduje się w obiekcie.

        Parameters
        ----------
        arg : str
            Nazwa pliku.
        """

        return arg in self.visible_files or (self.adj_tokens[0] is not None and arg == " prev") or (self.adj_tokens[0] is None and self.adj_tokens[1] is not None and arg == " next")

    def updateResults(self, forward=None):

        """
        Odśwież wyniki wyszukiwania lub przejdź na inną ich "stronę".

        Parameters
        ----------
        forward : bool or None, optional
            Czy poruszać się do przodu (True lub False). Jeśli None, to pobierana jest pierwsza strona wyszukiwania.
        """

        # to wybiera potrzebne nam dane
        files = lambda x: {i['snippet']['title'].replace('/', '\\'): YTStor(i['id']['videoId']) for i in x['items']}

        try:
            if self.adj_tokens[forward] is None: #na wypadek, gdyby ktoś jakimś cudem chciał przekroczyć granicę
                forward = None
        except KeyError:
            pass

        try:
            try:
                data = self.avail_files[ self.adj_tokens[forward] ] #może dane są już dostępne lokalnie.
            except KeyError:
                recv = self.__search( self.adj_tokens[forward] ) #ni ma, szukamy
                data = (None, files(recv)) #ujednolicamy format, trochę.
                                                                                                 
        except KeyError: #nie siadł indeks w adj_tokens

            if forward is None:
                recv = self.__search()
                data = (None, files(recv)) #też
            else:
                raise ValueError("Valid values for forward are True, False or None (default).")

        if len(self.avail_files) > 4:
            pop = self.avail_files.popitem(False) #wyrzucamy najstarsze dane
            for s in pop.values(): s.clean()

        adj_t = deepcopy(self.adj_tokens) # to zaraz wpiszemy do avail_files, teraz uaktualniamy self.adj_tokens.

        if data[0] is None: #bierzemy tokeny z pobranych wyników.
            try:
                self.adj_tokens[False] = recv['prevPageToken']
            except KeyError:
                self.adj_tokens[False] = None

            try:
                self.adj_tokens[True] = recv['nextPageToken']
            except KeyError:
                self.adj_tokens[True] = None

        else: #mamy z avail_files.
            self.adj_tokens = data[0]

        if forward is not None:
            #wrzucamy ostatnie wyniki do avail_files:
            self.avail_files[ self.adj_tokens[not forward] ] = (adj_t, self.visible_files)

        self.visible_files = data[1]

    def clean(self):

        """Wyczyść dane. Dla każdego obiektu YTStor zawartego w tym obiekcie wykonywana jest metoda clean."""

        for s in self.visible_files.values():
            s.clean()
        for s in [sub[x] for sub in self.avail_files.values() for x in sub]: # podwójne wyrażenia listowe są jednak
            s.clean()                                                        # średnio czytelne...
