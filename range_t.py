from copy import deepcopy
from threading import Event

class range_t():

    """
    Klasa pozwalająca na prosty zapis wielu zakresów w jednym obiekcie (multiple range).
    Podzakresy są reprezentowane przez dwuelementowe krotki, gdzie pierwszy element to lewy kraniec przedziału, a drugi
    to prawy. Lewy jest zawsze domknięty, a prawy zawsze otwarty (analogicznie jak w obiekcie typu range).

    Attributes
    ----------
    __has: set
        Zbiór podzakresów.
    waitings: dict
        Słownik zakresów, na które mogą oczekiwać wątki. Kluczem jest zakres, wartością obiekt threading.Event

    Parameters
    ----------
    initset: set, optional
        Początkowy zbiór składowych podzakresów. Domyślnie pusty.
    """

    def __init__(self, initset=set()):

        self.__has = set() #zbiór posiadanych zakresów
        self.waitings = dict()

        if not isinstance(initset, set):
            raise TypeError("Expected set of tuples")

        for t in initset:
            if not isinstance(t, tuple) or len(t) != 2 or t[1] <= t[0] or t[1] < 0:
                raise ValueError("Your tuples are wrong :(")

        self.__has = initset
        self.__optimize()

    def __match_l(self, k, set_):

        """
        Metoda szukająca zachodzących na k podzakresów ze zbioru set_.

        Parameters
        ----------
        k: tuple or list or range
            Zakres, dla którego sprawdzamy nachodzące podzakresy z set_.
        set_: set
            Zbiór podzakresów.

        Returns
        -------
        matched: set
            Zbiór podzakresów ze zbioru set_ zachodzących na k.
        """

        return {r for r in set_ if k[0] in range(*r) or k[1] in range(*r) or (k[0] < r[0] and k[1] >= r[1])}
                                   #k częściowo lub w całości w r            #r zawiera się w całości w k
    def __optimize(self):

        """
        Połącz nachodzące na siebie lub stykające się podzakresy zapisane w atrybucie __has. Wywoływane z wszystkich
        metod, które modyfikują zawartość obiektu.

        Returns
        -------
        None
        """

        ret = []

        for (begin, end) in sorted(self.__has):

            if ret and begin <= ret[-1][1] < end: # jeśli bieżący zakres zachodzi na ostatni z ret
                ret[-1] = (ret[-1][0], end)
            elif not ret or begin > ret[-1][1]:
                ret.append( (begin, end) )

        self.__has = set(ret)

        self.checkWaitings() #sprawdzamy, czy ktoś na nas nie czeka, może pojawiły się nowe zakresy?

    def __val_convert(self, val): #chyba przerobię to na dekorator dla wszystkich funkcji, które dostają val.

        """
        Konwertuj dane wejściowe na krotkę (start, end)

        Parameters
        ----------
        val: int or tuple or list or range
            Dwuelementowy obiekt przedstawiający zakres lub liczba całkowita.

        Returns
        -------
        converted: tuple
            Krotka reprezentująca zakres.
        """

        converted = (0, 0) #to tak w razie czego...

        #zamiana val na krotkę (start, end):

        if isinstance(val, range) and 0 <= val.start < val.stop and val.step == 1:

            converted = (val.start, val.stop)

        elif (isinstance(val, tuple) or isinstance(val, list)) and 0 <= val[0] < val[1] and len(val) == 2:

            converted = val

        elif isinstance(val, int):
            converted = (val, val+1)

        else:
            raise ValueError("Expected indexed positive value of lenght 2, integer or range of step 1")

        return converted

    def contains(self, val):

        """
        Sprawdź, czy dana wartość lub zakres jest zawarta w obiekcie.

        Parameters
        ----------
        val: int or tuple or list or range
            Badany zakres lub liczba całkowita.

        Returns
        -------
        retlen: int
            Długość pokrywających się z val obszarów.
        """

        (start, end) = self.__val_convert(val) #konwersja

        retlen = 0
        for r in self.__has:
            if start < r[1] and end > r[0]:
                retlen += ((end < r[1] and end) or r[1]) - ((start > r[0] and start) or r[0]) #chyba mam bzika na punkcie zwięzłego kodu :x

        return retlen

    def __contains__(self, val):

        """
        Metoda pozwalająca na użycie operatora in.

        Parameters
        ----------
        val: int or tuple or list or range
            Badany zakres lub liczba całkowita.

        Returns
        -------
        bool
            True, jeśli cały badany zakres zawiera się w obiekcie. W przeciwnym razie False.
        """
        
        conv = self.__val_convert(val) #konwersja
        return self.contains(val) == conv[1] - conv[0]

    def match(self, val):

        """
        Znajdź pokrywające się z val podzakresy. De facto jest widocznym wrapperem ukrytego __match_l.

        Parameters
        ----------
        val: int or tuple or list or range
            Badany zakres lub liczba całkowita.

        Returns
        -------
        set
            Zbiór pokrywających się podzakresów.
        """
        
        conv = self.__val_convert(val) #konwersja

        return self.__match_l(conv, self.__has)

    def toset(self):

        """
        Konwersja obiektu na zbiór podzakresów

        Returns
        -------
        set
            Zwracany jest ukryty atrybut __has.
        """

        return self.__has

    def __add(self, val):

        """
        Metoda pomocnicza, dodawanie zakresów. możliwe jest dodawanie jednego spójnego podzakresu naraz, albo
        obiektu range_t.

        Parameters
        ----------
        val: int or tuple or list or range
            Liczba całkowita lub zakres przeznaczony do dodania.

        Returns
        -------
        __has: set
            Zbiór self.__has poszerzony o nowy przedział.
        """

        if not isinstance(val, range_t):
            #sanitize it, bo czemu nie. przy okazji sprawdzamy, czy dane wejściowe są ok.
            val = {self.__val_convert(val)} #przerabiamy na zbiór, bo tak mi wygodnie.

        else:
            val = val.toset()

        __has = deepcopy(self.__has) #po prostu dodajemy do zbioru
        __has.update(val)

        return __has

    def __add__(self, val):

        """
        Obsługa operacji a + b.

        Parameters
        ----------
        val: int or tuple or list or range
            Liczba całkowita lub zakres przeznaczony do dodania.

        Returns
        -------
        range_t
            Nowy obiekt range_t poszerzony o val.
        """

        return range_t(self.__add(val))

    def __iadd__(self, val):

        """
        Obsługa operacji a += b. Różni się od __add__ tym, że nie jest tworzony nowy obiekt.

        Parameters
        ----------
        val: int or tuple or list or range
            Liczba całkowita lub zakres przeznaczony do dodania.

        Returns
        -------
        self: range_t
            Zwracany jest bieżący obiekt poszerzony o val.
        """

        self.__has = self.__add(val)
        self.__optimize()

        return self

    def __sub__(self, val):

        """
        Odejmowanie (na analogicznych zasadach co dodawanie).
        
        Parameters
        ----------
        val: int or tuple or list or range
            Liczba całkowita lub zakres przeznaczony do odjęcia.

        Returns
        -------
        range_t
            Obiekt range_t pozbawiony val.
        """

        if not isinstance(val, range_t):
            #sanitize it!
            val = {self.__val_convert(val)} # j/w
        else:
            val = val.toset()

        __has = deepcopy(self.__has)

        for v in val:
            common = self.__match_l(v, __has) #szukamy kolidujących podzakresów
            if not common: continue #brak kolizji - nic do odjęcia.

            __has.difference_update(common) #usuwamy kolizje, bo musimy je przeciąć

            minmax = (min({l[0] for l in common}), max({r[1] for r in common}))
            #z kolizyjnych podzakresów zawsze dostaniemy po odjęciu dwa podzakresy albo jeden, jeśli v zachodzi na
            #jeden podzakres jednym końcem
            if minmax[0] < v[0]: __has.add((minmax[0], v[0]))
            if minmax[1] > v[1]: __has.add((v[1], minmax[1]))

        return range_t(__has)

    def __len__(self):

        """
        Długość obiektu.

        Returns
        -------
        ret: int
            Suma długości posiadanych podzakresów.
        """

        ret = 0
        for t in self.__has:
            ret += t[1] - t[0]

        return ret

    def __eq__(self, val):

        """
        Operacja porównania.

        Parameters
        ----------
        val: range_t
            Obiekt range_t do porównania.

        Returns
        -------
        bool
            True, jeśli zbiór posiadanych podzakresów jest identyczny jak w obiekcie val.
        """
        if not isinstance(val, range_t):
            raise ValueError("Expected range_t to compare.")

        return self.__has == val.toset()

    def checkWaitings(self):

        """
        Sprawdź, czy zakresy z self.waitings nie zostały uzupełnione. Jeśli tak, to wyemituj zdarzenie i usuń zakres
        ze słownika.
        """

        to_rem = set()
        for e in (e for e in self.waitings if e in self):
            s = self.waitings[e].set()

        for x in to_rem:
            del self.waitings[x]

    def setWaiting(self, val):
        
        """
        Zaczekaj na dodanie zakresu do obiektu.

        Parameters
        ----------
        val: int or tuple or list or range
            Liczba całkowita lub zakres, na który chcemy zaczekać
        """

        conv = self.__val_convert(val) #konwersja

        if conv in self: return # już jest :)

        print("w")

        self.waitings[conv] = Event() # tworzymy zdarzenie i ...
        self.waitings[conv].wait() # ... czekamy
