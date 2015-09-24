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
from copy import deepcopy
from io import BytesIO

from .range_t import range_t

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
    lock : Lock
        Lock to sync multiple threads.
    fds : set
        Set of file descriptors assigned to the object.
    closing : bool
        ``True`` if ``data`` is scheduled for closing.
    avail : range_t
        Object saying how much data we have.
    filesize : int
        Total data size. Not yet downloaded data is also considered.
    disk : int
        How much data is cached on disk (8M factor).
    extension : str
        File extension.
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
    init_data : dict
        Initial data object needed for further operation. ``YTStor`` needs ``yid`` (str, YouTube video id) and
        ``pub_date`` (video publication date as Unix timestamp).
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

    def __init__(self, init_data, opts=dict()):

        yid = init_data['yid'] # it must be here.

        if self.rickastley:
            yid = "dQw4w9WgXcQ" #trolololo

        if not isinstance(yid, str) or len(yid) != 11:
            raise ValueError("yid expected to be valid Youtube movie identifier") #FIXME

        self.data = tempfile.SpooledTemporaryFile()
        self.fds = set()
        self.closing = False

        self.lock = Lock() # lock to prevent threads from colliding

        self.avail = range_t()
        self.safe_range = range_t()
        self.processing_range = range_t()

        self.filesize = 4096
        self.disk = 0
        self.extension = ".mp4" # FIXME

        self.atime = int(time())
        try:
            # convert from iso 8601
            self.ctime = timegm(datetime.strptime(init_data['pub_date'], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        except KeyError:
            self.ctime = self.atime

        self.r_session = requests.Session()

        self.yid = yid

        _pref = deepcopy(self.preferences) # new object, just to not affect other intances.
        try: _pref['audio'] = opts['audio']
        except KeyError: pass
        try: _pref['video'] = opts['video']
        except KeyError: pass
        try: _pref['format'] = opts['format']
        except KeyError: pass
        try: _pref['stream'] = opts['stream']
        except KeyError: pass
        try: _pref['get_info_on_init'] = opts['get_info_on_init']
        except KeyError: pass
        self.preferences = _pref

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

        # - for easy sorting - we'll get best quality and lowest filsize
        aud = {(-int(f['abr']),    f['filesize'], f['url']) for f in info['formats'] if 'audio' in f['format'] and 'abr' in f}
        vid = {(-int(f['height']), f['filesize'], f['url']) for f in info['formats'] if 'video' in f['format'] and 'height' in f}
        full= {(-int(f['height']), f['filesize'], f['url']) for f in info['formats'] if 'DASH' not in f['format'] and 'height' in f}

        try:
            _f = int( self.preferences.get('format') ) # if valid format is present, then choose closes value
            _k = lambda x: abs(x[0] + _f) # +, because x[0] is negative

        except (ValueError, TypeError):
            _k = lambda d: d

        if self.preferences['audio'] and self.preferences['video']: fm = min(full, key=_k)
        elif self.preferences['audio']: fm = min(aud, key=_k)
        elif self.preferences['video']: fm = min(vid, key=_k)

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

        self.fds.add(fh)
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

        self.lock.acquire()

        try:
            dl = range_t({safe}) - self.avail

            for r in dl.toset():
                Downloader.fetch(self, r, fh) # download is, let's say, atomic thanks to lock

            if self.disk + 1 < len(self.avail):

                self.data.rollover()
                self.disk += 1

        finally:
            self.lock.release()

        self.data.seek(offset)
        return self.data.read(length) #FIXME - error handling

    def clean(self):

        """
        Clear data. Explicitly close ``self.data`` if object is unused.
        """

        self.closing = True # schedule for closing.

        if not self.fds:
            self.data.close()

    def unregisterHandler(self, fh):

        """
        Unregister a file descriptor. Clean data, if such operation has been scheduled.

        Parameters
        ----------
        fh : int
            File descriptor.
        """

        try:
            self.fds.remove(fh)

        except KeyError:
            pass

        self.lock.acquire()

        try:
            self.data.rollover() # rollover data on close.

        finally:
            self.lock.release()

        if self.closing and not self.fds:
            self.data.close()

class YTMetaStor():

    """
    Class that holds metadata in a seperate file. Should always correspond to existing *Stor object, though this
    relation isn't held anywhere in *Stor objects, they'll just share a filename, but with different extensions.
    """

    # TODO: docs

    extension = ""

    def __init__(self, init_data, opts=dict()):

        self.data = BytesIO()

        self.atime = int(time())
        try:
            # convert from iso 8601
            self.ctime = timegm(datetime.strptime(init_data['pub_date'], "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        except KeyError:
            self.ctime = self.atime

        if not init_data.get('url'):

            self.data.write(bytes(init_data['title'], 'utf-8') + b" [" + bytes(init_data['yid'], 'utf-8')
                    + b"]\nby: " + bytes(init_data['channel'], 'utf-8') + b" at: "
                    + bytes(init_data['pub_date'], 'utf-8') + b"\n\n" + bytes(init_data['desc'], 'utf-8') + b"\n")

            self.url = None

        else:
            url = init_data['url']
            self.data.write(requests.get(url).content)

        self.filesize = self.data.tell()

    def obtainInfo(self):
        "Just return."
        return True

    def registerHandler(self, fh):

        "Update atime."

        self.atime = int(time())

    def read(self, offset, length, fh):

        """
        Read data.

        Parameters
        ----------
        offset : int
            Read offset.
        length : int
            Length of data.
        fh : int
            File descriptor, ignored.
        """

        self.data.seek(offset)
        return self.data.read(length)

    def clean(self):

        """
        Close file-like object.
        """

        self.data.close()

    def unregisterHandler(self, fh):
        "Just pass."
        pass
