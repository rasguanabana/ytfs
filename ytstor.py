class Downloader():

    """
    Klasa odpowiedzialna za pobieranie danych
    """

    @staticmethod
    def fetch(yts, needed_range):

        pass

class YTStor():

    """
    YTStor - serce YTFS. Klasa odpowiedzialna za zdobywanie i przechowywanie danych oraz informacji o filmie o podanym
    identyfikatorze.

    ### doc dla init
    """

    def __init__(self, yid):

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier")

        self.yid = yid

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
