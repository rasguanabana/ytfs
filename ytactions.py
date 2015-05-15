class YTActions():

    """
    Klasa pozwalająca na realizowanie operacji wyszukiwania filmów w serwisie YouTube oraz przechowująca informacje o
    wynikach wyszukiwania.

    ### doc dla init
    """

    visible_files = dict()  # Słownik wiążący tytuł filmu z obiektem YTStor. Zawiera tylko te pliki, które mają być
                            # w danej chwili widoczne dla użytkownika (bez plików sterujących).
                            # 
                            # visible_files = {
                            #                   "Foo": YTStor(yid),
                            #                   ...
                            #                 }

    def __init__(self, search_query, start = 0, end = 10):

        if not isinstance(search_query, str):
            raise ValueError("Expected str for 1st parameter (search_query).")
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValueError("Expected int for 2nd (start) and 3rd (end) parameters.")

        self.search_query = search_query
        self.start = start
        self.end = end

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

        return arg in self.visible_files or (self.start != 0 and arg == " prev") or arg == " next"

    def updateBounds(self, start=None, end=None, dir_=0):

        pass
