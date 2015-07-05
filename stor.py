"""
Module responsible for downloading multimedia from Internet services. As for now only YouTube is supported.
"""

import os
import youtube_dl
import requests
import tempfile
from time import time, sleep
from threading import Thread, Event

from range_t import range_t

class Downloader():

    """
    Class responsible for data downloading. Every object similiar to ``YTStor`` can use it. (Currently no class, other
    than aforementioned ``YTStor``, is capable of using ``Downloader``).
    """

    class FetchError(Exception):
        pass

    @staticmethod
    def fetch(yts, needed_range, fh):

        """
        Download desired range of data and put it in `yts` object (e.g. ``YTStor``).

        Parameters
        ----------
        yts : YTStor
            Stor-like object to which we will write.
        needed_range : tuple
            Two element tuple that represents a data range - compliant with ``range_t`` subrange definition.
        fh : int
            Descriptor used by a process for filesystem operations.
        
        Returns
        -------
        None
            Method does not return; data is written directly to `yts` object.
        """

        if yts.SET_AV == YTStor.DL_AUD | YTStor.DL_VID:

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as d, tempfile.NamedTemporaryFile(prefix='a') as a, tempfile.NamedTemporaryFile(prefix='v') as v:
                # after with statement, files - save d - shall be removed

                v.write(yts.r_session.get(yts.info[0]['url']).content) # download video
                a.write(yts.r_session.get(yts.info[1]['url']).content) # download audio

                PP = youtube_dl.postprocessor.FFmpegMergerPP(yts.ytdl)
                PP.run({'filepath': d.name, '__files_to_merge': (v.name, a.name)}) # merge

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
            yts.data.seek(hr[0])            #SET_AV equals 2 or 1
            yts.data.write(get.content)
            yts.data.flush()

            ret = list( int(s) for s in get.headers.get('content-range').split(' ')[1].split('/')[0].split('-') )
            ret[1] += 1

            yts.avail += tuple(ret)
            yts.processing_range -= needed_range


class YTStor():

    """
    YTStor - serce YTFS. Klasa odpowiedzialna za zdobywanie i przechowywanie danych oraz informacji o filmie o podanym
    identyfikatorze.
    ``YTStor`` - the heart of YTFS. Class responsible for obtaining and storing data and information about a movie of
    given id.

    Attributes
    ----------
    data : SpooledTemporaryFile
        Temporary file object - actual data is stored here.
    global_dl_lock : bool
        Global download lock. Used when merge of audio and video is needed because all data has to be downloaded
        at once.
    thread : list
        List of running ``Downloader`` threads.
    avail : range_t
        Object saying how much data we have.
    safe_range : range_t
        Range contained in ``avail``. It constitutes these data ranges, whose read won't cause reading process to wait
        for download of new data.
    processing_range : range_t
        Range of data being currently processed. Thanks to that, given thread can check if data, which it want to
        download, isn't already being downloaded by another thread.
    filesize : int
        Total data size. Not yet downloaded data is also considered.
    r_session : requests.Session
        Object that holds HTTP session. Thanks to that, we avoid useless TCP window size negotiations whenever we
        start a download.
    yid : str
        YouTube id of a video which this object represents.
    info : dict
        A dictionary wich contains info about movie data being downloaded. More precisely, it is a dict one can find
        under ``'requested_formats'`` key in ``YoutubeDL.extract_info`` function result.

    DL_VID : int
        Constant, which written to SET_AV, will instruct object to download video data.
    DL_AUD : int
        Constant, which written to SET_AV, will instruct object to download audio data.
    SET_AV : int
        Attribute wich stores information about what kind of data object will download. It consists of combination of
        DL_VID and DL_AUD.

    Parameters
    ----------
    yid : str
        YouTube video id.
    """

    DL_VID = 0b10
    DL_AUD = 0b01
    SET_AV = 0b11

    @staticmethod
    def _setDownloadManner(av):

        """
        Static method that sets the attibute which instructs ``Downloader`` what it will download (``SET_AV``).

        Parameters
        ----------
        av : int
            Two bit number, whose bits tells what ``Downloader`` shall download. The first bit is responsible for
            audio, the second bit for video. For value assignment ``YTStor.DL_AUD`` and ``YTStor.DL_VID`` constants are
            used.  Attention: when audio and video data download is selected, then download and merge are performed
            during ``open`` system call. Otherwise, audio/video data is downloaded dynamically on ``read``.
        """

        if not (isinstance(av, int) and 0 <= av <= 3):
            raise ValueError("av needs to be combination of YTStor.DL_AUD and YTStor.DL_VID");

        if av == 0: av = YTStor.DL_AUD # audio downloading is default.

        YTStor.SET_AV = av

    def __init__(self, yid):

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier") #FIXME

        self.data = tempfile.SpooledTemporaryFile()
        self.global_dl_lock = False
        self.thread = []

        self.avail = range_t()
        self.safe_range = range_t()
        self.processing_range = range_t()
        self.spooled = 1;

        self.filesize = 4096

        self.r_session = requests.Session()

        self.yid = yid
        self.ytdl = youtube_dl.YoutubeDL({"quiet": True, "format": "bestvideo+bestaudio"})
        self.ytdl.add_info_extractor( self.ytdl.get_info_extractor("Youtube") )

    def obtainInfo(self):

        """
        Method for obtaining information about the movie.
        """

        self.info = self.ytdl.extract_info(self.yid, download=False)['requested_formats']
        try:
            self.filesize = self.info[2 - self.SET_AV]['filesize']
        except (KeyError, IndexError):
            pass

        return True #FIXME
    
    def registerHandler(self, fh): # Do I even need that? possible FIXME.

        """
        Regidter new file descriptor.

        Parameters
        ----------
        fh : int
            Deskryptor pliku.
        """

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
                self.avail.setWaiting(fh) # wait for anything, beacause all data is downloaded at once. fh is unique.
        
    def read(self, offset, length, fh):

        """
        Read data. Method returns data instantly, if they're avaialable and in ``self.safe_range``. Otherwise data is
        downloaded and then returned.

        Parameters
        ----------
        start : int
            Left boundary of desired data range.
        end : int
            Right boundary of desired data range.
        fh : int
            File descriptor.
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
        if self.processing_range.contains(need): # needed range overlaps with currently processed.

            ws += self.processing_range - (self.processing_range - need) # to make that simplier, range_t should be updated FIXME

        if current not in self.safe_range: # data is read outside of ``self.safe_range`` - we have to download a bit.

            dls = range_t({need}) - self.avail # missing data range.
            dls -= ws # we substract ranges, that we wait for, because somebody else takes care of them.

            self.processing_range += dls

            for r in dls.toset():
                _t = Thread( target=Downloader.fetch, args=(self, r, fh) ) # download
                _t.daemon = True
                _t.start()
                self.thread.append(_t)

            self.avail.setWaiting(need) # wait for data we need to be ready.

            self.safe_range += safe

            #if offset > self.spooled * 2 * 1024**2: # zapisujemy dane na dysk
            #    self.data.rollover()
            #    self.spooled += 1

        # done, we can return data:

        self.data.seek(offset)
        return self.data.read(length) #FIXME - error handling

    def clean(self):

        """
        Clear data. Explicitly close ``self.data``. Additionaly, call join() on threads started earlier.
        """

        self.data.close()

        for t in self.thread:
            t.join(1)
        #TODO mark object as unusable.
