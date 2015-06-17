import os
import youtube_dl
import requests
import tempfile
from time import time, sleep
from threading import Event

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

            ind = yts.SET_AV - 1 #SET_AV jest równe 1 albo 2

            yts.data.write(yts.r_session.get(yts.info[1 - ind]['url']).content)
            yts.data.flush()
            yts.filesize = yts.info[1 - ind]['filesize']

            yts.avail += (0, yts.filesize)

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
        self.filesize = 4096

        self.r_session = requests.Session()

        self.yid = yid
        self.ytdl = youtube_dl.YoutubeDL({"quiet": True})
        self.ytdl.add_info_extractor( self.ytdl.get_info_extractor("Youtube") )

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

        self.info = self.ytdl.extract_info(self.yid, download=False)['requested_formats']
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

        if (0, self.filesize) not in self.avail and True: #FIXME - zamiast True sprawdzać av czy jest a+v

            if not self.global_dl_lock:

                print("DL-ing")
                self.global_dl_lock = True

                #try:
                Downloader.fetch(self, None, fh)
                #except:
                #    self.avail.waitings[(0,1)].set()
                #    del self.avail.waitings[(0,1)]

                self.global_dl_lock = False
                print("DL-ed")

            elif self.global_dl_lock:

                print("WAITING")
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

        #r = (offset, offset + length)

        #if self.avail.contains(r) < length:
        #    Downloader.fetch(self, r, fh)
        #else:
        #    print("!!!!!!!!!!!!!!!!!!!!!")

        #print(self.avail.toset())

        self.data.seek(offset)
        return self.data.read(length) #FIXME - sprawdzanie błędów

    #def clean(self, all_data=False):
    #    
    #    """ """
    #    pass
