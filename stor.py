"""
Module responsible for downloading multimedia from Internet services. As for now only YouTube is supported.
"""

import os
import youtube_dl
import requests
import tempfile
from time import time, sleep
from calendar import timegm
from datetime import datetime
from threading import Lock

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

        if yts.preferences['audio'] and yts.preferences['video'] and isinstance(yts.url, tuple) and not yts.preferences['stream']:
            #condition for merging.

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as d, tempfile.NamedTemporaryFile(prefix='a') as a, tempfile.NamedTemporaryFile(prefix='v') as v:
                # after with statement, files - save d - shall be removed

                v.write(yts.r_session.get(yts.url[0]).content)
                a.write(yts.r_session.get(yts.url[1]).content)

                PP = youtube_dl.postprocessor.FFmpegMergerPP(yts.ytdl)
                PP.run({'filepath': d.name, '__files_to_merge': (v.name, a.name)}) # merge

                _d = d.name

            with open(_d, mode="rb") as d:

                yts.data.write( d.read() )
                yts.data.flush()

                yts.filesize = os.path.getsize(_d)

                yts.avail += (0, yts.filesize)

            os.remove(_d)

        else: # no merging

            if yts.preferences['stream'] is False: # preload

                yts.data.write(yts.r_session.get(yts.url).content)
                yts.data.flush()

                yts.avail += (0, yts.filesize)

            else: # stream

                hr = (needed_range[0], needed_range[1] - 1)

                get = yts.r_session.get(yts.url, headers={'Range': 'bytes=' + '-'.join(str(i) for i in hr)})

                yts.data.seek(hr[0])
                yts.data.write(get.content)
                yts.data.flush()

                ret = list( int(s) for s in get.headers.get('content-range').split(' ')[1].split('/')[0].split('-') )
                ret[1] += 1

                yts.avail += tuple(ret)
                yts.processing_range -= needed_range

class YTStor():

    """
    ``YTStor`` - the heart of YTFS. Class responsible for obtaining and storing data and information about a movie of
    given id.

    Attributes
    ----------
    data : SpooledTemporaryFile
        Temporary file object - actual data is stored here.
    closed : bool
        ``True`` if ``data`` was closed.
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
    rickastley : bool
        Make every video rickroll
    r_session : requests.Session
        Object that holds HTTP session. Thanks to that, we avoid useless TCP window size negotiations whenever we
        start a download.
    yid : str
        YouTube id of a video which this object represents.
    preferences : dict
        Current object preferences.
    url : str or tuple
        Url to file. If tuple, then merging is needed; indices: 0: video, 1: audio.

    Parameters
    ----------
    yid : str
        YouTube video id.
    opts : dict
        Options that will override globally set preferences.
    """

    preferences = {
        "audio": True,
        "video": True,
        "stream": True,
        "get_info_on_init": False
    }

    rickastley = False

    def __init__(self, yid, opts=dict()):

        if self.rickastley:
            yid = "dQw4w9WgXcQ" #trolololo

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier") #FIXME

        self.data = tempfile.SpooledTemporaryFile()
        self.lock = Lock() # lock to prevent threads from colliding

        self.avail = range_t()
        self.safe_range = range_t()
        self.processing_range = range_t()

        self.filesize = 4096

        self.atime = int(time())
        try:
            # convert from iso 8601
            self.ctime = timegm(datetime.strptime(opts['pub_date'], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        except KeyError:
            self.ctime = self.atime

        self.r_session = requests.Session()

        self.yid = yid

        try: self.preferences['audio'] = opts['audio']
        except KeyError: pass
        try: self.preferences['video'] = opts['video']
        except KeyError: pass
        try: self.preferences['stream'] = opts['stream']
        except KeyError: pass
        try: self.preferences['get_info_on_init'] = opts['get_info_on_init']
        except KeyError: pass

        self.ytdl = youtube_dl.YoutubeDL({"quiet": True, "format": "bestvideo+bestaudio"})
        self.ytdl.add_info_extractor( self.ytdl.get_info_extractor("Youtube") )

    def obtainInfo(self):

        """
        Method for obtaining information about the movie.
        """

        info = self.ytdl.extract_info(self.yid, download=False)

        if not self.preferences['stream']:
            self.url = (info['requested_formats'][0]['url'], info['requested_formats'][1]['url'])
            return True

        # else:
        for f in info['formats']:
            if 'filesize' not in f:
                f['filesize'] = 'x' # next line won't fail, str for the sorting sake.

        # - 10000 for easy sorting - we'll get best quality and lowest filsize
        aud = {(10000 - int(f['abr']),    f['filesize'], f['url']) for f in info['formats'] if 'audio' in f['format']}
        vid = {(10000 - int(f['height']), f['filesize'], f['url']) for f in info['formats'] if 'video' in f['format']}
        full= {(10000 - int(f['height']), f['filesize'], f['url']) for f in info['formats'] if 'DASH' not in f['format']}

        if self.preferences['audio'] and self.preferences['video']: fm = min(full)
        elif self.preferences['audio']: fm = min(aud)
        elif self.preferences['video']: fm = min(vid)

        self.url = fm[2]
        if fm[1] == 'x':
            self.filesize = int(self.r_session.head(self.url).headers['content-length'])
        else:
            self.filesize = int(fm[1])

        return True

    def registerHandler(self, fh): # Do I even need that? possible FIXME.

        """
        Register new file descriptor.

        Parameters
        ----------
        fh : int
            File descriptor.
        """

        self.atime = int(time()) # update access time

        self.lock.acquire()

        try:
            if (0, self.filesize) not in self.avail and self.preferences['stream'] is False:

                Downloader.fetch(self, None, fh) # lock forces other threads to wait, so fetch will perform just once.

        finally:
            self.lock.release()

    def read(self, offset, length, fh):

        """
        Read data. Method returns data instantly, if they're avaialable and in ``self.safe_range``. Otherwise data is
        downloaded and then returned.

        Parameters
        ----------
        offset : int
            Read offset
        length : int
            Length of data to read.
        fh : int
            File descriptor.
        """

        current = (offset, offset + length)

        safe = [ current[0] - ( 8 * length ), current[1] + ( 16 * length ) ]
        if safe[0] < 0: safe[0] = 0
        if safe[1] > self.filesize: safe[1] = self.filesize
        safe = tuple(safe)

        ##need = [ safe[0] - ( 8 * length ), safe[1] + ( 16 * length ) ]
        ##if need[0] < 0: need[0] = 0
        ##if need[1] > self.filesize: need[1] = self.filesize
        ##need = tuple(need)

        ##ws = range_t()
        ##if self.processing_range.contains(need): # needed range overlaps with currently processed.

        ##    ws += self.processing_range - (self.processing_range - need) # to make that simplier, range_t should be updated FIXME

        ##if current not in self.safe_range: # data is read outside of ``self.safe_range`` - we have to download a bit.

        ##    dls = range_t({need}) - self.avail # missing data range.
        ##    dls -= ws # we substract ranges, that we wait for, because somebody else takes care of them.

        ##    self.processing_range += dls

        ##    for r in dls.toset():
        ##        _t = Thread( target=Downloader.fetch, args=(self, r, fh) ) # download
        ##        _t.daemon = True
        ##        _t.start()
        ##        self.thread.append(_t)

        ##    self.avail.setWaiting(need) # wait for data we need to be ready.

        ##    self.safe_range += safe

            #if offset > self.spooled * 2 * 1024**2: # zapisujemy dane na dysk
            #    self.data.rollover()
            #    self.spooled += 1

        # done, we can return data:

        self.lock.acquire()

        try:
            dl = range_t({safe}) - self.avail

            for r in dl.toset():
                Downloader.fetch(self, r, fh) # download is, let's say, atomic thanks to lock

        finally:
            self.lock.release()

        self.data.seek(offset)
        return self.data.read(length) #FIXME - error handling

    def clean(self):

        """
        Clear data. Explicitly close ``self.data``.
        """

        self.data.close()
        self.closed = True
