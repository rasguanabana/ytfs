import requests

from ytstor import YTStor

from copy import copy, deepcopy

class YTActions():

    """
    Klasa pozwalająca na realizowanie operacji wyszukiwania filmów w serwisie YouTube oraz przechowująca informacje o
    wynikach wyszukiwania.

    ### doc dla init
    """

    visible_files = dict()      # Słownik wiążący tytuł filmu z obiektem YTStor. Zawiera tylko te pliki, które mają być
                                # w danej chwili widoczne dla użytkownika (bez plików sterujących).
                                # 
                                # visible_files = {
                                #                   "Foo": YTStor(yid),
                                #                   ...
                                #                 }

    page_tokens = [None, None]  # Tokeny służące do wczytywania następnych/poprzednich stron wyników wyszukiwania
    last_dir = None             # Ostatnio obrany kierunek w nawigowaniu po wynikach wyszukiwania FIXME: threads

    def __init__(self, search_query, max_results = 10):

        if not isinstance(search_query, str):
            raise ValueError("Expected str for 1st parameter (search_query).")
        if not isinstance(max_results, int):
            raise ValueError("Expected int for 2nd parameter (max_results).")

        self.search_query = search_query
        self.max_results = max_results

    def __search(self, pt=None):

        """ """

        api_fixed_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&fields=items(id%2Ckind%2Csnippet)%2CnextPageToken%2CprevPageToken"
        api_key = "AIzaSyCPOg5HQfHayQH6mRu4m2PMGc3eHd5lllg"

        url = "{0}&key={1}&maxResults={2}&q={3}&pageToken=".format(api_fixed_url, api_key, self.max_results, self.search_query)

        try:
            url += pt
        except TypeError:
            pass

        return requests.get(url).json() #FIXME? trochę gołe, a coś może pójść nie tak...

    def __iter__(self):

        if self.start != 0:
            ctrl = [' prev', ' next']
        else:
            ctrl = [' next']

        self.vf_iter = iter(ctrl + list(self.visible_files))

        return self

    def __next__(self):

        return next(self.vf_iter)

    def __getitem__(self, key):

        return self.visible_files[key]

    def __in__(self, arg):

        return arg in self.visible_files or (self.page_tokens[0] is not None and arg == " prev") or (self.page_tokens[0] is None and self.page_tokens[1] is not None and arg == " next") #FIXME? cza sprawdzić

    def updateResults(self, dir_=None):

        """
        Odśwież wyniki wyszukiwania lub przejdź na inną ich "stronę".

        Parameters
        ----------
        dir_: int or None, optional
            Kierunek przemieszczania się w wynikach wyszukiwania. 0 - strona do tyłu, 1 - strona do przodu.

        Returns
        -------
        None
        """

        #FIXME to można zrobić ładniej... i tak żeby działało :v

        if (dir_ == 0 and self.last_dir == 1) or (dir_ == 1 and self.last_dir == 0):
            # kierunek jest odwrotny do poprzedniego, więc zamieniamy bieżacy słownik z backupem
            # (przy okazji zapewniamy, że zmienne są dobrego typu)

            (self.backup_vfiles, self.visible_files) = (self.visible_files, self.backup_vfiles)
            (self.backup_pt, self.page_tokens) = (self.page_tokens, self.backup_pt)
            self.last_dir = dir_
            return

        try:
            if dir_ < 0: dir_ = 2 #chcemy, żeby try się wysypał
            data = self.__search(self.page_tokens[dir_])

        except IndexError:
            raise ValueError("Valid values for dir_ are 0 or 1")
        except TypeError:
            data = self.__search() # dir_ jest innego typu niż int, więc zajmujemy się pierwszą stroną wyników

        self.backup_pt = deepcopy(self.page_tokens)
        try:
            self.page_tokens[0] = data['prevPageToken']
        except KeyError:
            self.page_tokens[0] = None

        try:
            self.page_tokens[1] = data['nextPageToken']
        except KeyError:
            self.page_tokens[1] = None

        self.backup_vfiles = copy(self.visible_files)
        self.visible_files = { i['snippet']['title']: YTStor(i['id']['videoId']) for i in data['items'] }

        if dir_ is not None:
            self.last_dir = dir_
