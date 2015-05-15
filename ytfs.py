#!/usr/bin/python3

####                                                                                                                  #
###  Przed lekturą kodu zaleca się zapoznianie z instrukcją użytkownika, w celu ułatwienia zrozumienia zachodzących  ##
##   tu procesów.                                                                                                   ###
#                                                                                                                  ####

import os
import stat
import errno
from enum import Enum
from copy import deepcopy

from fuse import FUSE, FuseOSError, Operations

from ytstor import YTStor
from ytactions import YTActions

class fd_dict(dict):

    def push(self, yts):

        """
        Rozszerzenie, które znajduje najniższy niewykorzystany deskryptor i wpisuje podeń krotkowy identyfikator
        filmu.

        Parameters
        ----------
        yts: YTStor-obj or None
            Obiekt YTStor, dla którego chcemy przydzielić deskryptor lub None, jeśli alokujemy deskryptor dla
            pliku sterującego.
     
        Returns
        -------
        descriptor : int
            Deskryptor do pliku.
        """

        if not isinstance(yts, (YTStor, type(None)):
            raise TypeError("Expected YTStor object or None.")

        k = 0
        while k in self.keys():
            k += 1
        self[k] = yts

        return k


class YTFS(Operations):

    """Główna klasa ytfs :)"""

    __sh_script = b"#!/bin/sh\n" #zawartość pliku sterującego (pusty skrypt)

    def __init__(self):

        """Inicjalizacja obiektu"""

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
                                #       'wyszukiwana fraza 1':  YTActions({
                                #                                'tytul1': <YTStor obj>,
                                #                                'tytul2': <YTStor obj>,
                                #                                ...
                                #                               }),
                                #       'wyszukiwana fraza 2':  YTActions({ ... }),
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

    class PathType(Enum):

        """Czytelna reprezentacja typu podanego identyfikatora krotkowego."""

        invalid = 0
        main = 1
        subdir = 2
        file = 3
        ctrl = 4

        @staticmethod
        def get(p):

            """
            Sprawdź typ ścieżki

            Parameters
            ----------
            p : str or tuple
                Ścieżka do pliku lub identyfikator krotkowy

            Returns
            -------
            path_type : PathType
                Typ pliku jako enumerator PathType

            """

            try:
                p = self.__pathToTuple(p) #próba konwersji, jeśli p jest stringiem. inaczej nic się nie stanie
            except TypeError:
                pass

            if not isinstance(p, tuple) or len(p) != 2 or not (isinstance(p[0], (str, type(None))) and isinstance(p[1], (str, type(None)))):
                return YTFS.PathType.invalid

            elif p[0] is None and p[1] is None:
                return YTFS.PathType.main

            elif p[0] and p[1] is None:
                return YTFS.PathType.subdir

            elif p[0] and p[1]:
                
                if p[0][0] = ' ':
                    return YTFS.PathType.ctrl
                else:
                    return YTFS.PathType.file

            else:
                return YTFS.PathType.invalid

    def __pathToTuple(self, path):

        """
        Konwersja ścieżki do katalogu lub pliku na jego identyfikator krotkowy.

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

    def __exists(self, p):

        """
        Sprawdź czy plik o podanej ścieżce istnieje.

        Parameters
        ----------
        p : str or tuple
            Ścieżka do pliku

        Returns
        -------
        exists : bool
            True, jeśli plik istnieje. W przeciwnym razie False.

        """

        if not isinstance(p, tuple) and isinstance(p, str):
            tid = self.__pathToTuple(p)

        return ((not tid[0] and not tid[1]) or (tid[0] in self.searches and not tid[1]) or (tid[0] in self.searches and
            tid[1] in self.searches[tid[0]]))

    def _pathdec(method):

        """Dekorator podmieniający argument path z reprezentacji tekstowej na identyfikator krotkowy."""

        def mod(self, *args):

            args = list(args)
            try:
                args[0] = self.__pathToTuple(args[0])
            except ValueError:
                raise FuseOSError(errno.EINVAL)

            return method(self, *args)

        return mod

    @_pathdec
    def getattr(self, tid, fh=None):

        """Atrybuty pliku."""

        if not self.__exists(tid):
            raise FuseOSError(errno.ENOENT)

        pt = self.PathType.get(tid)

        st = deepcopy(self.st)
        st['st_atime'] = int(time())
        st['st_mtime'] = st['st_atime']
        st['st_ctime'] = st['st_atime']

        if pt is self.PathType.file:
            
            st['st_mode'] = stat.S_IFREG | 0o444
            st['st_nlink'] = 1

            st['st_size'] = self.searches[tid[0]][tid[1]].SIZE #TODO

        elif pt is self.PathType.ctrl:

            st['st_mode'] = stat.S_IFREG | 0o555 #te uprawnienia chyba trzeba ciutkę podreperować
            st['st_nlink'] = 1
            st['st_size'] = len(self.__sh_script)

        return st

    @_pathdec
    def readdir(self, tid, fh):

        """Listowanie katalogu."""

        ret = []
        pt = self.PathType.get(tid)
        try:
            if pt is self.PathType.main:
                ret = list(self.searches)

            elif pt is self.PathType.subdir:
                ret = list(self.searches[tid[0]])

            elif pt is self.PathType.file:
                raise FuseOSError(errno.ENOTDIR)

            else:
                raise FuseOSError(errno.ENOENT)

        except KeyError:
            raise FuseOSError(errno.ENOENT)

        return ['.', '..'] + ret

    @_pathdec
    def mkdir(self, tid, mode):

        """Utworzenie katalogu."""

        pt = self.PathType.get(tid)

        if pt is self.PathType.invalid or pt is self.PathType.file:
            raise FuseOSError(errno.EPERM)

        if self.__exists(tid):
            raise FuseOSError(errno.EEXIST)

        self.searches[tid[0]] = YTActions(tid[0])

        return 0

    @_pathdec
    def rmdir(self, tid):

        """Usunięcie katalogu."""

        pt = self.PathType.get(tid)

        if pt is self.PathType.main:
            raise FuseOSError(errno.EINVAL)
        elif pt is not self.PathType.subdir:
            raise FuseOSError(errno.ENOTDIR)

        try:
            del self.searches[tid[0]]

        except KeyError:
            raise FuseOSError(errno.ENOENT)

        return 0

    @_pathdec
    def open(self, tid, flags):

        """Otwarcie pliku."""

        pt = self.PathType.get(tid)

        if pt is not self.PathType.file and pt is not self.PathType.ctrl:
            raise FuseOSError(errno.EINVAL)

        if flags & os.O_WRONLY or flags & os.O_RDWR:
            raise FuseOSError(errno.EROFS)

        if not self.__exists(tid):
            raise FuseOSError(errno.ENOENT)

        yts = self.searches[tid[0]][tid[1]]

        try:
            if yts.INIT(): #TODO odwołanie do obiektu YTstor
                return self.fds.push(yts) #zwracamy deskryptor (powiązanie z YTStor)
            else:
                raise FuseOSError(errno.ENOENT) #FIXME? nie wiem czy pasi

        except AttributeError:
            return self.fds.push(None) #zwracamy deskryptor (nie potrzeba żadnego powiązania dla pliku sterującego)

    @_pathdec
    def read(self, tid, length, offset, fh):

        """Odczyt z pliku."""

        try:
            return self.fds[fh].READ(offset, offset + length) #TODO

        except AttributeError: #plik sterujący

            d = (tid[1] == " next" and 1) or (tid[1] == " prev" and -1) or 0

            try:
                self.searches[tid[0]].updateBounds(dir_ = d)
            except KeyError:
                raise FuseOSError(errno.EINVAL) #no coś nie pykło

            return self.__sh_script[offset:offset+length] #FIXME? w razie jakby zakres był zły

        except KeyError: #deskryptor nie istnieje
            raise FuseOSError(errno.EBADF)

    @_pathdec
    def release(self, tid, fh):

        """Zamknięcie pliku (?)"""

        try:
            del self.fds[fh]

        except KeyError:
            raise FuseOSError(errno.EBADF)

        return 0
