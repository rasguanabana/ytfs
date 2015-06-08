import youtube_dl
import requests
import tempfile
from time import time

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

        yts.data.write(yts.r_session.get(yts.info['url']).content)
        yts.data.flush()

#        yts.dl_control[fh].idle = False
#
#        r_ran = list(needed_range)
#        r_len = 0
#
#        while r_len != needed_range[1] - needed_range[0]:
#
#            r_ran[0] += r_len #przesuwamy lewą granicę, jeśli coś już pobraliśmy
#
#            #pobieramy kawałek (w obrębie sesji, więc trzymamy jedno połączenie tcp)
#            recv = yts.r_session.get(yts.info['url'], headers={'Range': 'bytes=' + str(r_ran[0]) + "-" + str(r_ran[1] - 1)})
#
#            print("DBG", recv.content[0:128], recv.content[-128:])
#
#            try:
#                r_len += yts.data.write(recv.content)
#                yts.data.flush()
#            except:
#                raise Downloader.FetchError("!")
#
#            yts.avail += tuple(r_ran) #pobrane, więc odnotowujemy, że mamy taki dane.
#
#        yts.dl_control[fh].idle = True
#        yts.dl_control[fh].abort = False


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

    Parameters
    ----------
    yid: str
        Identyfikator wideo YouTube.
    """

    data = None
    dl_control = None
    avail = None
    r_session = None
    info = None

    __ytdl = None

    class DlControl():
        idle = True
        abort = False

    def __init__(self, yid):

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier")

        self.data = tempfile.SpooledTemporaryFile()
        self.dl_control = dict()
        self.avail = range_t()
        self.r_session = requests.Session()
        self.info = {'filesize': 4096}

        self.yid = yid
        self.__ytdl = youtube_dl.YoutubeDL({"quiet": True})
        self.__ytdl.add_info_extractor( self.__ytdl.get_info_extractor("Youtube") )

    #def prepare():

    #    """
    #    Przygotuj obiekt do pobierania. Tworzone są wymagane ku temu atrybuty klasy.

    #    Parameters
    #    ----------
    #    None

    #    Returns
    #    -------
    #    None
    #    """

    #    self.data = tempfile.SpooledTemporaryFile()
    #    self.dl_control = None #TODO

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

        self.info = self.__ytdl.extract_info(self.yid, download=False)['requested_formats'][1]
        return True #FIXME

    #def setFormat(self, fmt):

    #    """ """
    #    pass
    
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
        Downloader.fetch(self, None, fh)
        
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

        #r = (offset, offset + length)

        #if self.avail.contains(r) < length:
        #    Downloader.fetch(self, r, fh)
        #else:
        #    print("!!!!!!!!!!!!!!!!!!!!!")

        #print(self.avail.toset())

        self.data.seek(offset) #?
        return self.data.read(length) #FIXME - sprawdzanie błędów

    #def clean(self, all_data=False):
    #    
    #    """ """
    #    pass
