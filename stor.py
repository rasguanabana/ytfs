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

        av = yts.opts.get('av', yts.SET_AV)

        if av == YTStor.DL_AUD | YTStor.DL_VID and yts.url.get("audio") and yts.url.get("video") and not yts.streaming:
            #condition for merging.

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as d, tempfile.NamedTemporaryFile(prefix='a') as a, tempfile.NamedTemporaryFile(prefix='v') as v:
                # after with statement, files - save d - shall be removed

                v.write(yts.r_session.get(yts.url['video']).content)
                a.write(yts.r_session.get(yts.url['audio']).content)

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

            if av == YTStor.DL_AUD:
                print('aud')
                url = yts.url['audio']
            elif av == YTStor.DL_VID:
                print('vid')
                url = yts.url['video']
            elif av == YTStor.DL_VID | YTStor.DL_AUD:
                print('full')
                url = yts.url['full']

            if yts.streaming is False: # preload

                yts.data.write(yts.r_session.get(url).content)
                yts.data.flush()

                yts.avail += (0, yts.filesize)

            else: # stream

                hr = (needed_range[0], needed_range[1] - 1)

                get = yts.r_session.get(url, headers={'Range': 'bytes=' + '-'.join(str(i) for i in hr)})
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
    streaming : bool
        Whether to stream content or download all at once.
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
    opts : dict
        Options provided to ``__init__``
    url : dict
        A dictionary containing urls to content. Keys:
        `video`: video url,
        `audio`: audio url,
        `full`:  url to movie with both audio and video.
        Values may be ``None`` if url is not present.

    DL_VID : int
        Constant, which written to SET_AV, will instruct object to download video data.
    DL_AUD : int
        Constant, which written to SET_AV, will instruct object to download audio data.
    SET_AV : int
        Attribute wich stores information about what kind of data object will download. It consists of combination of
        DL_VID and DL_AUD. DL_AUD is default value.

    SET_STREAM : bool or None
        ``True``: try streaming whenever possible (quality might be lower).
        ``False``: always load whole data before reading.
        ``None``: decide automatically.

    SET_FMT : str or None
        Custom, yet global, user specified format. ``None`` by default.
    FALLBACK : str
        If custom format isn't found or not specified then this will be chosen.

    RICKASTLEY : bool
        Make every video rickroll

    Parameters
    ----------
    yid : str
        YouTube video id.
    """

    DL_VID = 0b10
    DL_AUD = 0b01
    SET_AV = 0b01

    SET_STREAM = None

    SET_FMT = None
    FALLBACK_FMT = "bestvideo[height<=?1080]+bestaudio/best"

    RICKASTLEY = False

    def __init__(self, yid, opts=dict()):

        if self.RICKASTLEY:
            yid = "dQw4w9WgXcQ" #trolololo

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
        self.opts = opts

        self.url = dict()

        fmt = "/".join(f for f in [opts.get('format'), self.SET_FMT, self.FALLBACK_FMT] if f and isinstance(f, str))

        self.ytdl = youtube_dl.YoutubeDL({"quiet": True, "format": fmt})
        self.ytdl.add_info_extractor( self.ytdl.get_info_extractor("Youtube") )

    def obtainInfo(self):

        """
        Method for obtaining information about the movie.
        """

        info = self.ytdl.extract_info(self.yid, download=False)

        # url:

        want_stream = self.opts.get('stream', self.SET_STREAM) # get value from opts, get SET_STREAM if not present.
        av = self.opts.get('av', self.SET_AV)

        get_filesize = None # whether to obtain filesize by HEAD http request

        try:
            if av == self.DL_AUD | self.DL_VID and want_stream and not tuple(f for f in info['formats'] if "DASH" not in f['format']):
                # user selected audio+video, prefers streaming and streamable formats are available

                self.streaming = True

                fmts = [info['formats'][-1]] # `best` equivalent. TODO make sure it's true.
                self.filesize = self.r_session.head(fmts['url'])['content-length']

            else:
                self.streaming = False if want_stream is False else None # False if False, None if True or None.

                fmts = info['requested_formats'] # got separate audio and video.
                self.filesize = fmts[2 - av]['filesize']

        except KeyError:

            if "+" in info['format']: # something went wrong, requested_formats should've been accessible
                raise ValueError #FIXME?

            fmts = [info]
            self.filesize = info['filesize']

        for el in fmts:

            if "audio" in el['format']:
                self.url['audio'] = el['url']

            elif "video" in el['format']:
                self.url['video'] = el['url']

            elif len(fmts) == 1:
                self.url['full'] = el['url']

            else:
                raise ValueError #FIXME? not sure if ValueError suits it.

        if (av == YTStor.DL_AUD and 'audio' in self.url) or (av == YTStor.DL_VID and 'video' in self.url) or (av == YTStor.DL_AUD | YTStor.DL_VID and (('audio' in self.url and 'video' in self.url) or 'full' in self.url)):
            return True
        else:
            return False
    
    def registerHandler(self, fh): # Do I even need that? possible FIXME.

        """
        Register new file descriptor.

        Parameters
        ----------
        fh : int
            File descriptor.
        """

        if (0, self.filesize) not in self.avail and self.streaming is False:

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
