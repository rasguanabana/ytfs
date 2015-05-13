from copy import deepcopy

class range_t():

    """klasa zakresów. służy do prostego zapisywania dostępnych zakresów danych
        prawe krańce są zawsze otwarte, lewe są zawsze zamknięte."""


    __has = set() #zbiór posiadanych zakresów
    def __init__(self, initset=set()):

        """inicjalizacja."""

        if not isinstance(initset, set):
            raise TypeError("Expected set of tuples")

        for t in initset:
            if not isinstance(t, tuple) or len(t) != 2 or t[1] <= t[0] or t[1] < 0:
                raise ValueError("Your tuples are wrong :(")

        self.__has = initset
        self.__optimize()
        #chyba dobrze by było zrobić asserta, który potwierdzi, że podobszary na siebie nie zachodzą. przynajmniej na czas testów.


    __match_l = lambda self, k, set_: {r for r in set_ if k[0] in range(*r) or k[1] in range(*r) or (k[0] < r[0] and k[1] >= r[1])}
                                                    #start lub end zawierają się w podzakresie, start i end okalają zakres
    def __optimize(self):

        """łączenie stykających się/nachodzących podzakresów"""

        #szukanie "kolizji" i sumowanie podzakresów:
        pre = deepcopy(self.__has)
        post = set()

        while pre:

            t = pre.pop()

            common = self.__match_l(t, pre).union({t})
            pre.difference_update(common) #usuwamy użyte podzakresy

            to_add = (min({l[0] for l in common}), max({r[1] for r in common}))
                            #minimum z lewych krańców, maksimum z prawych

            if self.__match_l(to_add, pre): #jeśli wynik nadal zachodzi na jakieś podzakresy, to wrzucamy go z powrotem.
                pre.add(to_add)
            else:
                post.add(to_add) #w przeciwnym razie dodajemy sumę do wyniku

        #spawanie:
        d = dict(post) #pomocniczy słownik
        l = list(d.keys()) #klucze, po których będziemy iterować

        (ret, used) = (set(), set())
        for start in l:
            if start in used: continue #chyba muszę zamienić na while'a

            end = start
            try:
                while True:
                    end = d[end] #czaisz magię? krotki (start, end) zostały zamienione na start: end, zatem, jeśli podzakresy się stykają, to end będzie początkiem innego podzakresu, a więc kluczem w słowniku, pod którym jest koniec, albo kolejny indeks.
                    used.add(end)
            except KeyError: #end nie jest kluczem, więc przerywamy while'a.
                ret.add((start, end))
        
        self.__has = ret #iii zapis!

    def __val_convert(self, val): #chyba przerobię to na dekorator dla wszystkich funkcji, które dostają val.

        """konwertuje dane wejściowe na krotkę (start, end)"""

        converted = (0, 0)

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

        """sprawdza, czy dana wartość lub zakres jest zawarta w zakresie.
            zwraca długość pokrywających się zakresów."""

        (start, end) = self.__val_convert(val) #konwersja

        retlen = 0
        for r in self.__has:
            if start < r[1] and end > r[0]:
                retlen += ((end < r[1] and end) or r[1]) - ((start > r[0] and start) or r[0]) #chyba mam pierdolca na punkcie zwięzłego kodu :x

        return retlen

    def __contains__(self, val):
        return bool(self.contains(val))

    def match(self, val):

        """zwraca pokrywające się z val podzakresy"""
        
        conv = self.__val_convert(val) #konwersja

        return self.__match_l(conv, self.__has)
        #return sorted([r for r in self.__has if start in range(*r) or end in range(*r) or (start < r[0] and end >= r[1])]) #jak wyżej XD
                                                #start lub end zawierają się w podzakresie, start i end okalają zakres

    def toset(self):

        return self.__has

    def __add__(self, val):

        """dodawanie zakresów. możliwe jest dodawanie jednego spójnego podzakresu naraz, albo obiektu range_t."""

        if not isinstance(val, range_t):
            #sanitize it, bo czemu nie. przy okazji sprawdzamy, czy dane wejściowe są ok.
            val = {self.__val_convert(val)} #przerabiamy na zbiór, bo tak mi wygodnie.

        else:
            val = val.toset()

        __has = deepcopy(self.__has) #po prostu dodajemy do zbioru, następnie zwracamy niu abdżekt
        __has.update(val)

        return range_t(__has)

    def __sub__(self, val):

        """odejmowanie (na analogicznych zasadach co dodawanie)."""

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
            #z kolizyjnych podzakresów zawsze dostaniemy po odjęciu dwa podzakresy albo jeden, jeśli v zachodzi na jeden podzakres jednym końcem
            if minmax[0] < v[0]: __has.add((minmax[0], v[0]))
            if minmax[1] > v[1]: __has.add((v[1], minmax[1]))

        return range_t(__has)

    def __len__(self):

        """suma długości spójnych podzakresów."""

        ret = 0
        for t in self.__has:
            ret += t[1] - t[0]

        return ret

    def __eq__(self, val):

        """=="""
        if not isinstance(val, range_t):
            raise ValueError("Expected range_t to compare.")

        return self.__has == val.toset()

#    def diff(self, val): #wygląda na niepotrzebne...
#
#        """zwraca niezawierające się w zakresie podzbióry val"""
#        val = self.__val_convert(val)
#        #zakresy kolizyjne:
#        common = self.__match_l(val, self.__has) #zbieramy podzakresy kolizyjne
#        lav = range_t({val}) #przerabiamy val na range_t, a dalej magic :)
#
#        for sr in common:
#            lav -= sr
#
#        return lav # \o/
