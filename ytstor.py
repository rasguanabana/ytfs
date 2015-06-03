import requests

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
        yts : YTStor-obj
            Obiekt YTStor, do którego będziemy pisać
        needed_range : tuple
            Dwuelementowa krotka oznaczająca zakres danych (start, end). Przedział jest lewostronnie domknięty.
        
        Returns
        -------
        None
            Metoda niczego nie zwraca; dane są bezpośrednio wpisywane do obiektu YTStor.
        """

        yts.data_control[fh]['idle'] = False

        stream = requests.get(yts.download_url, stream=True, headers={'Range', 'bytes='+needed_range.join('-')})

        #TODO - śledzenie bieżącej pozycji w pliku
        
        for chunk in stream.iter_content(chunk_size=1024):

            if yts.data_control[fh]['abort'] == True:
                break

            if chunk:
                try:
                    yts.data.write(chunk)
                    yts.data.flush()
                    #yts.avail + #TODO - dopisanie zakresu do range_t
                except:
                    raise Downloader.FetchError("!")

        yts.data_control[fh]['idle'] = True


class YTStor():

    """
    YTStor - serce YTFS. Klasa odpowiedzialna za zdobywanie i przechowywanie danych oraz informacji o filmie o podanym
    identyfikatorze.

    ### doc dla init
    """

    data = None
    data_control = None

    def __init__(self, yid):

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier")

        self.yid = yid

    def prepare():

        """
        Przygotuj obiekt do pobierania. Tworzone są wymagane ku temu atrybuty klasy.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.data = tempfile.SpooledTemporaryFile()
        self.data_control = None #TODO

    def obtainInfo(self):

        """ """
        pass

    def setFormat(self, fmt):

        """ """
        pass
        
    def read(self, start, end, fh):

        """ """
        pass

    def clean(self, all_data=False):
        
        """ """
        pass
