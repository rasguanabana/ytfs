import os
import youtube_dl
import requests
import tempfile
from time import time, sleep
from threading import Thread, Event

from range_t import range_t

class Downloader():

    """
    Klasa odpowiedzialna za pobieranie danych
    """

    class FetchError(Exception):
        pass

    @staticmethod
    def fetch(yts, needed_range, fh):

        """
        Pobierz żądany zakres danych i umieść je w obiekcie YTStor.

        Parameters
        ----------
        yts : YTStor
            Obiekt YTStor, do którego będziemy pisać
        needed_range : tuple
            Dwuelementowa krotka oznaczająca zakres danych (start, end). Przedział jest lewostronnie domknięty.
        
        Returns
        -------
        None
            Metoda niczego nie zwraca; dane są bezpośrednio wpisywane do obiektu YTStor.
        """

        print(".")

        if yts.SET_AV == YTStor.DL_AUD | YTStor.DL_VID:

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as d, tempfile.NamedTemporaryFile(prefix='a') as a, tempfile.NamedTemporaryFile(prefix='v') as v:
                # po opuszczeniu with pliki zostaną usunięte

                v.write(yts.r_session.get(yts.info[0]['url']).content) #pobieramy wideo
                a.write(yts.r_session.get(yts.info[1]['url']).content) #pobieramy audio

                PP = youtube_dl.postprocessor.FFmpegMergerPP(yts.ytdl)
                PP.run({'filepath': d.name, '__files_to_merge': (v.name, a.name)}) #łączymy

                _d = d.name

            with open(_d, mode="rb") as d:

                yts.data.write( d.read() )
                yts.data.flush()
                yts.filesize = os.path.getsize(_d)

                yts.avail += (0, yts.filesize)

            os.remove(_d)

        else:

            hr = (needed_range[0], needed_range[1] - 1)

            get = yts.r_session.get(yts.info[2 - yts.SET_AV]['url'], headers={'Range': 'bytes=' + '-'.join(str(i) for i in hr)})
            yts.data.seek(hr[0])
            yts.data.write(get.content)
            yts.data.flush()                            #SET_AV równa się 2 lub 1

            ret = list( int(s) for s in get.headers.get('content-range').split(' ')[1].split('/')[0].split('-') )
            ret[1] += 1

            yts.avail += tuple(ret)
            yts.processing_range -= needed_range


class YTStor():

    """
    YTStor - serce YTFS. Klasa odpowiedzialna za zdobywanie i przechowywanie danych oraz informacji o filmie o podanym
    identyfikatorze.

    Attributes
    ----------
    data: SpooledTemporaryFile
        Obiekt pliku tymczasowego, który przechowuje pobrane dane.
    dl_control: DlControl
        Obiekt zawierający zmienne sterujące dla Downloaderów (osobne zestawy dla różnych deskryptorów).
    avail: range_t
        Obiekt mówiący o tym ile danych posiadamy.
    r_session: requests.Session
        Obiekt trzymający sesję HTTP.
    yid: str
        Identyfikator wideo YouTube.
    info: dict
        ... #FIXME

    Parameters
    ----------
    yid: str
        Identyfikator wideo YouTube.
    """

    DL_VID = 0b10
    DL_AUD = 0b01
    SET_AV = 0b11

    class DlControl():
        idle = True
        abort = False

    @staticmethod
    def _setDownloadManner(av):

        """
        Metoda statyczna ustawiająca atrybut mówiący downloaderowi co ma pobierać.

        Parameters
        ----------
        av: int
            Liczba dwubitowa, której bity mówią o tym co pobieramy. Pierwszy bit odpowiada za audio, drugi za wideo.
            Do przypisania wartości można użyć wartości YTStor.DL_AUD oraz YTStor.DL_VID. Uwaga: jeśli zaznaczono
            pobieranie audio i wideo, wówczas pobieranie i łączenie dokonuje się podczas wywołania open, w przeciwnym
            razie audio/wideo są pobierane dynamicznie (TODO).
        """

        if not (isinstance(av, int) and 0 <= av <= 3):
            raise ValueError("av needs to be combination of YTStor.DL_AUD and YTStor.DL_VID");

        if av == 0: av = YTStor.DL_AUD #domyślnie pobieramy audio

        YTStor.SET_AV = av

    def __init__(self, yid):

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier")

        self.data = tempfile.SpooledTemporaryFile()
        self.dl_control = dict()
        self.global_dl_lock = False

        self.avail = range_t()
        self.safe_range = range_t()
        self.processing_range = range_t()

        self.filesize = 4096

        self.r_session = requests.Session()

        self.yid = yid
        self.ytdl = youtube_dl.YoutubeDL({"quiet": True})
        self.ytdl.add_info_extractor( self.ytdl.get_info_extractor("Youtube") )

    def obtainInfo(self):

        """
        Metoda pozyskująca informacje o filmie
        
        Parameters
        ----------
        None

        Returns
        -------
        None
            Metoda nie zwraca, natomiast w razie niepowodzenia może rzucać wyjątki.
        """

        self.info = self.ytdl.extract_info(self.yid, download=False)['requested_formats']
        self.filesize = self.info[2 - self.SET_AV]['filesize']

        return True #FIXME
    
    def registerHandler(self, fh):

        """
        Zarejestruj nowy deskryptor.

        Parameters
        ----------
        fh: int
            Deskryptor pliku.

        Returns
        -------
        None
        """

        self.dl_control[fh] = YTStor.DlControl()

        if (0, self.filesize) not in self.avail and self.SET_AV == YTStor.DL_AUD | YTStor.DL_VID:

            if not self.global_dl_lock:

                self.global_dl_lock = True

                #try:
                Downloader.fetch(self, None, fh)
                #except:
                #    self.avail.waitings[(0,1)].set()
                #    del self.avail.waitings[(0,1)]

                self.global_dl_lock = False

            elif self.global_dl_lock:
                self.avail.setWaiting(fh) # czekamy na cokolwiek, bo i tak preload wypełnia cały plik. fh jest unikalny
        
    def read(self, offset, length, fh):

        """
        Odczytaj dane. Metoda zwraca dane natychmiast, jeśli są dostępne, lub, w razie potrzeby, pobiera je.

        Parameters
        ----------
        start: int
            Lewy kraniec żądanego zakresu.
        end: int
            Prawy kraniec żądanego zakresu.
        fh: int
            Deskryptor pliku.

        Returns
        -------
        None
        """

        current = (offset, offset + length)

        safe = [ current[0] - ( 8 * length ), current[1] + ( 16 * length ) ]
        if safe[0] < 0: safe[0] = 0
        if safe[1] > self.filesize: safe[1] = self.filesize
        safe = tuple(safe)

        need = [ safe[0] - ( 8 * length ), safe[1] + ( 16 * length ) ]
        if need[0] < 0: need[0] = 0
        if need[1] > self.filesize: need[1] = self.filesize
        need = tuple(need)

        ws = range_t()
        if self.processing_range.contains(need): # zakres, którego potrzebujemy, jakoś pokrywa się z przetwarzanymi.

            ws += self.processing_range - (self.processing_range - need) # można optymalniej, trzeba zaktualizować range_t FIXME

        if current not in self.safe_range: # próba odczytu danych zza safe_range - musimy trochę dociągnąć

            dls = range_t({need}) - self.avail # brakujące zakresy danych.
            dls -= ws # wywalamy zbiory, na które musimy poczekać, bo zajmuje się nimi ktoś inny.

            self.processing_range += dls

            thread = []
            for r in dls.toset():
                thread.append(Thread( target=Downloader.fetch, args=(self, r, fh) )) # zlecamy pobieranie
                thread[-1].daemon = True
                thread[-1].start()

            self.avail.setWaiting(need) # czekamy aż to czego potrzebujemy będzie gotowe

            for t in thread:
                t.join()

            self.safe_range += safe

        # zrobione, można zwrócić dane:

        self.data.seek(offset)
        return self.data.read(length) #FIXME - sprawdzanie błędów
