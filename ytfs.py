#!/usr/bin/python3

####                                                                                                                  #
###  Przed lekturą kodu zaleca się zapoznianie z instrukcją użytkownika, w celu ułatwienia zrozumienia zachodzących  ##
##   tu procesów.                                                                                                   ###
#                                                                                                                  ####

import os
import stat

from fuse import FUSE, FuseOSError, Operations

class fd_dict(dict):

    def push(self, path):

        """Rozszerzenie, które znajduje najniższy niewykorzystany deskryptor i wpisuje podeń krotkowy identyfikator
        filmu.
        
        Parameters
        ----------
        path : array-like
            Krotkowy identyfikator pliku, dla którego chcemy przydzielić deskryptor.
        
        Returns
        -------
        descriptor : int
            Deskryptor do pliku.
        """

        k = 0
        while k in self.keys():
            k += 1
        self[k] = path

        return k


class YTFS(Operations):

    """Główna klasa ytfs :)"""

    def __init__(self):

        """Inicjalizacja obiektu""" #TODO: wszystko inne poza szkieletem klasy :v

        self.st = {

            'st_mode': stat.S_IFDIR | 0o555,
            'st_ino': 0,
            'st_dev': 0,
            'st_nlink': 2,
            'st_uid': os.getuid(),
            'st_gid': os.getgid(),
            'st_size': 4096,
            'st_atime': 0,
            'st_mtime': 0,
            'st_ctime': 0
        }
                                # Uwaga: dla uproszczenia rozszerzenia w nazwach plików są obecne wyłącznie podczas
                                # wypisywania zawartości katalogu. We wszelkich innych operacjach są upuszczane.

        self.searches = dict()  # Słownik będący głównym interfejsem do przechowywanych przez system plików danych
                                # o poszczególnych wyszukiwaniach i ich wynikach, czyli filmach. Struktura:
                                #
                                #   {
                                #       'wyszukiwana fraza 1':  {
                                #                                'tytul1': <YTStor obj>,
                                #                                'tytul2': <YTStor obj>,
                                #                                ...
                                #                               },
                                #       'wyszukiwana fraza 2':  { ... },
                                #       ...
                                #   }
                                #
                                # Obiekt YTStor przechowuje wszystkie potrzebne informacje o filmie, nie tylko dane
                                # dane multimedialne.

        self.fds = dict()       # Słownik fd_dict wiążący będące w użyciu deskryptory z identyfikatorami filmów.
                                # Klucz: deskryptor
                                # Wartość: krotka (katalog, nazwa pliku bez rozszerzenia)
                                # Przykład:
                                #
                                # {
                                #       1: ('wyszukiwana fraza 1', 'tytul1':

    def __pathToTuple(self, path):

        """Konwersja ścieżki do katalogu lub pliku na jego identyfikator krotkowy.

        Parameters
        ----------
        path : str
            Ścieżka do skonwertowania. Może przybrać postać /, /katalog, /katalog/ lub /katalog/nazwa_pliku.

        Returns
        -------
        tup_id : tuple
            Dwuelementowy krotkowy identyfikator katalogu/pliku postaci (katalog, nazwa_pliku). Jeśli ścieżka prowadzi
            do katalogu głównego, to oba pola krotki przyjmą wartość None. Jeśli ścieżka prowadzi do katalogu
            wyszukiwania, to pole nazwa_pliku przyjmie wartość None.

        Raises
        ------
        ValueError
            W przypadku podania nieprawidłowej ścieżki
        """

        if not path or path.count('/') > 2:
            raise ValueError("Bad path given") #pusta ścieżka "" albo zbyt głęboka

        try:
            split = path.split('/')
        except (AttributeError, TypeError):
            raise TypeError("Path has to be string") #path nie jest stringiem

        if split[0]:
            raise ValueError("Path needs to start with '/'") #path nie zaczyna się od "/"
        del split[0]

        try:
            if not split[-1]: split.pop() #podana ścieżka kończyła się ukośnikiem
        except IndexError:
            raise ValueError("Bad path given") #przynajmniej jeden element w split powinien na tę chwilę istnieć

        if len(split) > 2:
            raise ValueError("Path is too deep. Max allowed level i 2") #ścieżka jest zbyt długa

        try:
            d = split[0]
        except IndexError:
            d = None
        try:
            f = split[1]
        except IndexError:
            f = None

        if not d and f:
            raise ValueError("Bad path given") #jest nazwa pliku, ale nie ma katalogu #przypał

        return (d, f)

    def __exists(self, path):

        """Sprawdź czy plik o podanej ścieżce istnieje.

        Parameters
        ----------
        path : str
            Ścieżka do pliku

        Returns
        -------
        exists : bool
            True, jeśli plik istnieje. W przeciwnym razie False.

        """

        tid = self.__pathToTuple(path)

        return ((not tid[0] and not tid[1]) or (tid[0] in self.searches and not tid[1]) or (tid[0] in self.searches and
            tid[1] in self.searches[tid[0]]))

    def getattr(self, path, fh=None):

        """Atrybuty pliku."""

        pass

    def readdir(self, path, fh):

        """Listowanie katalogu."""

        pass

    def mkdir(self, path, mode):

        """Utworzenie katalogu."""
        pass

    def rmdir(self, path):

        """Usunięcie katalogu."""

        pass

    def open(self, path, flags):

        """Otwarcie pliku."""

        pass

    def read(self, path, length, offset, fh):

        """Odczyt z pliku."""

        pass

    def flush(self, path, fh):

        'Flush'

        pass
