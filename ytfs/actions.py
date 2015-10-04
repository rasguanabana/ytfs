"""
Module responsible for searching movies in Internet services. As for now only YouTube is supported.
"""

import os
import requests

from .stor import YTStor, YTMetaStor

from copy import copy, deepcopy
from collections import OrderedDict
from urllib.parse import urlencode

class YTActions():

    """
    Class responsible for searching in YouTube service and holding information about search results.

    Attributes
    ----------
    avail_files : OrderedDict
        Contains tuples of following format:

        avail_files = {
                        "token": (`adj_tokens`, `files`),
                        ...
                    }

        `adj_tokens` contains adjacent tokens, `files` contains files of given search.
        (just as described below).
    visible_files : dict
        Current search results. Key is a movie name, value is a ``YTStor`` object for given movie.
    adj_tokens : dict
        Dictionary of tokens for adjacent search pages. Under ``False`` key the previous page is kept, under ``True`` -
        the next. Other keys are not allowed.
    vf_iter : obj
        Here the ``YTActions`` obejct stores an iterator allowing for current directory content listing. Used by
        ``__iter__`` and ``__next__`` methods.
    search_params : dict
        Additional search params for __search.
    yts_opts : dict
        Custom options passed to YTStor objects created in this class.
    api_key : str
        YouTube API key.
    preferences : dict
        Current object preferences.

    Parameters
    ----------
    search_query : str
        Currently used search phrase.
    """

    api_key = "AIzaSyCPOg5HQfHayQH6mRu4m2PMGc3eHd5lllg"

    preferences = {
        "metadata": {
            "desc": False,
            "thumb": False
        }
    }

    def __init__(self, search_query):

        if not isinstance(search_query, str):
            raise ValueError("Expected str for 1st parameter (search_query).")

        self.avail_files = OrderedDict()
        self.visible_files = None
        self.adj_tokens = {False: None, True: None}

        self.vf_iter = None

        self.search_params = {"maxResults": 10,
                "order": self.preferences["order"]} # relevance by default
        self.yts_opts = dict()

        parsed = self.__searchParser(search_query)

        # search params
        self.search_params.update(parsed[0])

        # YTa options
        _pref = deepcopy(self.preferences) # new object, just to not affect other intances.
        if 'metadata' in parsed[1]:
            try:
                meta_list = parsed[1]['metadata'].split(',')
            except AttributeError:
                meta_list = []

            if 'desc' in meta_list: _pref['metadata']['desc'] = True
            else: _pref['metadata']['desc'] = False

            if 'thumb' in meta_list: _pref['metadata']['thumb'] = True
            else: _pref['metadata']['thumb'] = False

        self.preferences = _pref

        # YTs options
        self.yts_opts = parsed[1]

        if 'audio' in parsed[1] and 'video' not in parsed[1]: self.yts_opts['video'] = False
        if 'video' in parsed[1] and 'audio' not in parsed[1]: self.yts_opts['audio'] = False

        self.__getChannelId()

        if parsed[0].get("publishedBefore"): self.search_params["publishedBefore"] += "T00:00:00Z"
        if parsed[0].get("publishedAfter"): self.search_params["publishedAfter"] += "T00:00:00Z"

    def __getChannelId(self):

        """
        Obtain channel id for channel name, if present in ``self.search_params``.
        """

        if not self.search_params.get("channelId"):
            return

        api_fixed_url = "https://www.googleapis.com/youtube/v3/channels?part=id&maxResults=1&fields=items%2Fid&"
        url = api_fixed_url + urlencode({"key": self.api_key, "forUsername": self.search_params["channelId"]})
        get = requests.get(url).json()

        try:
            self.search_params["channelId"] = get['items'][0]['id']
            return # got it

        except IndexError:
            pass # try searching now...

        api_fixed_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&fields=items%2Fid&"
        url = api_fixed_url + urlencode({"key": self.api_key, "q": self.search_params['channelId']})
        get = requests.get(url).json()

        try:
            self.search_params["channelId"] = get['items'][0]['id']['channelId']

        except IndexError:
            del self.search_params["channelId"] # channel not found

    def __searchParser(self, query):

        """
        Parse `query` for advanced search options.

        Parameters
        ----------
        query : str
            Search query to parse. Besides a search query, user can specify additional search parameters and YTFS
            specific options. Syntax:
            Additional search parameters: ``option:value``. if `value` contains spaces, then surround it with
            parentheses; available parameters: `channel`, `max`, `before`, `after`, `order`.
            YTFS options: specify options between ``[`` and ``]``; Available options: `a`, `v`, `f`, `P`, `s`, `m`.
            If an option takes a parameter, then specify it beetween parentheses.

            Examples: ``channel:foo search query``, ``my favourite music [a]``,
            ``channel:(the famous funny cats channel) [vf(240)P] funny cats max:20``.

            Invalid parameters/options are ignored.

        Returns
        -------
        params : tuple
            Tuple: 0 - dictionary of url GET parameters; 1 - dictionary of YTStor options.
        """

        ret = dict()

        parse_params = True

        buf = ""
        ptr = ""

        p_avail = ("channel", "max", "before", "after", "order")

        opts = dict()
        par_open = False

        translate = {
            'a': 'audio',
            'v': 'video',
            'f': 'format',
            's': 'stream',
            'P': 'stream',
            'm': 'metadata',
            'max': 'maxResults',
            'channel': 'channelId',
            'before': 'publishedBefore',
            'after': 'publishedAfter',
            'order': 'order',
            '': 'q'
        }

        for i in query+' ':

            if parse_params:

                if not par_open:

                    if i == ' ': # flush buf

                        try:
                            if ret.get(translate[ptr]):
                                ret[ translate[ptr] ] += ' '
                            else:
                                ret[ translate[ptr] ] = ''

                            ret[ translate[ptr] ] += buf

                        except KeyError:
                            pass

                        ptr = ""
                        buf = ""

                    elif i == ':' and buf in p_avail:

                        ptr = buf
                        buf = ""

                    elif not buf and i == '[': # buf must be empty

                        parse_params = False
                        ptr = ""

                    elif i != '(':
                        buf += i

                elif not (par_open == 1 and i == ')'):
                    buf += i

                if i == '(': par_open += 1
                if par_open > 0 and i == ')': par_open -= 1


            else:

                if i == ']':

                    parse_params = True
                    par_open = False
                    ptr = ""
                    buf = ""

                elif ptr and not par_open and i == '(':
                    par_open = True

                elif par_open:

                    if i == ')':

                        try:
                            opts[ translate[ptr] ] = buf
                        except KeyError:
                            pass

                        par_open = False
                        buf = ""

                    else:
                        buf += i

                elif i.isalpha():

                    ptr = i

                    try:
                        opts[ translate[ptr] ] = not i.isupper()
                    except KeyError:
                        pass

        return (ret, opts)

    def __search(self, pt=""):

        """
        Method responsible for searching using YouTube API.

        Parameters
        ----------
        pt : str
            Token of search results page. If ``None``, then the first page is downloaded.

        Returns
        -------
        results : dict
            Parsed JSON returned by YouTube API.
        """

        if not self.search_params.get('q') and not self.search_params.get('channelId'):
            return {'items': []} # no valid query - no results.

        api_fixed_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&fields=items(id%2Ckind%2Csnippet)%2CnextPageToken%2CprevPageToken&"

        d = {"key": self.api_key, "pageToken": pt}
        d.update(self.search_params)
        url = api_fixed_url + urlencode(d)

        get = requests.get(url) #FIXME? something can go wrong here...
        if get.status_code != 200:
            return {'items': []} # no valid query - no results.

        return get.json()

    def __iter__(self):

        """
        Create an iterator. Method allows - in a simple manner - for obtaining a generator which contains filenames.
        The real generator is ``self.vf_iter``; YTActions object (used as iterator) is only a wrapper.

        Returns
        -------
        self : YTActions
            This very same object with ``self.vf_iter`` constructed and initialised.
        """

        ctrl = []

        if self.adj_tokens[False] is not None:
            ctrl += [ " prev" ]
        if self.adj_tokens[True] is not None:
            ctrl += [ " next" ]

        self.vf_iter = iter(ctrl + [e + self.visible_files[e].extension for e in self.visible_files])

        return self

    def __next__(self):

        """
        ``next()`` support. Returns next filename.

        Returns
        -------
        file_name : str
            Next filename from ``self.vf_iter.``
        """

        return next(self.vf_iter) #easy, ain't it?

    def __getitem__(self, key):

        """
        Read elements from ``YTActions`` object by using `key`. One can use object like a dict (and like a boss, ofc).

        Parameters
        ----------
        key : str
            The key (e.g. ``YTActions['Rick Astley - Never Gonna Give You Up.mp4']``).

        Returns
        -------
        YTStor
            ``YTStor`` object associated with name `key`.
        """

        _k = os.path.splitext(key)

        if _k[1] not in ('.txt', '.jpg'):
            key = _k[0]

        return self.visible_files[key]

    def __in__(self, arg):

        """
        Check, if movie of name `arg` is present in the object.

        Parameters
        ----------
        arg : str
            Filename.
        """

        _a = os.path.splitext(arg)

        if _a[1] not in ('txt', 'jpg'):
            arg = _a[0]

        return arg in self.visible_files or (self.adj_tokens[0] is not None and arg == " prev") or (self.adj_tokens[0] is None and self.adj_tokens[1] is not None and arg == " next")

    def updateResults(self, forward=None):

        """
        Reload search results or load another "page".

        Parameters
        ----------
        forward : bool or None, optional
            Whether move forwards or backwards (``True`` or ``False``). If ``None``, then first page is loaded.
        """

        # this choses data we need.
        files = lambda x: {
            i['snippet']['title'].replace('/', '\\'): YTStor(
                {'yid': i['id']['videoId'], 'pub_date': i['snippet']['publishedAt']},
                opts=self.yts_opts) for i in x['items']
        }
        descs = lambda x: {
            (i['snippet']['title'].replace('/', '\\') + '.txt'): YTMetaStor(
                {
                    'title': i['snippet']['title'],
                    'yid': i['id']['videoId'],
                    'desc': i['snippet']['description'],
                    'channel': i['snippet']['channelTitle'],
                    'pub_date': i['snippet']['publishedAt']
                },
                opts=dict()
            ) for i in x['items']
        }
        thumbs = lambda x: {
            (i['snippet']['title'].replace('/', '\\') + '.jpg'): YTMetaStor(
                {'url': i['snippet']['thumbnails']['high']['url'], 'pub_date': i['snippet']['publishedAt']}, opts=dict()
            ) for i in x['items']
        }

        try:
            if self.adj_tokens[forward] is None: # in case someone would somehow cross boundary.
                forward = None
        except KeyError:
            pass

        recv = None
        try:
            try:
                data = self.avail_files[ self.adj_tokens[forward] ] # maybe data is already available locally.
            except KeyError:
                recv = self.__search( self.adj_tokens[forward] ) # nope, we have to search.
        except KeyError: # wrong index in adj_tokens

            if forward is None:
                recv = self.__search()
            else:
                raise ValueError("Valid values for forward are True, False or None (default).")

        if recv is not None:

            _d = files(recv)
            if self.preferences['metadata']['desc']: _d.update(descs(recv))
            if self.preferences['metadata']['thumb']: _d.update(thumbs(recv))

            data = (None, _d) # little format unification.

        if len(self.avail_files) > 4:

            pop = self.avail_files.popitem(False) # get rid of the oldest data.
            for s in pop[1][1].values(): s.clean()

        adj_t = deepcopy(self.adj_tokens) # this will we write to avail_files, now we update self.adj_tokens.

        if data[0] is None: # get tokens from obtained results.
            try:
                self.adj_tokens[False] = recv['prevPageToken']
            except KeyError:
                self.adj_tokens[False] = None

            try:
                self.adj_tokens[True] = recv['nextPageToken']
            except KeyError:
                self.adj_tokens[True] = None

        else: # already in avail_files.
            self.adj_tokens = data[0]

        if forward is not None:
            # backup last results in avail_files:
            self.avail_files[ self.adj_tokens[not forward] ] = (adj_t, self.visible_files)

        self.visible_files = data[1]

    def clean(self):

        """Clear the data. For each ``YTStor`` object present in this object ``clean`` method is executed."""

        for s in self.visible_files.values():
            s.clean()
        for s in [sub[1][x] for sub in self.avail_files.values() for x in sub[1]]: # Double list comprehensions aren't very
            s.clean()                                                        # readable...
