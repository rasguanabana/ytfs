"""
Module responsible for searching movies in Internet services. As for now only YouTube is supported.
"""

import os
import requests

from stor import YTStor

from copy import copy, deepcopy
from collections import OrderedDict

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

    Parameters
    ----------
    search_query : str
        Currently used search phrase.
    max_results : int, optional
        Number of results for a single "page".
    """

    avail_files = OrderedDict()
    visible_files = None
    adj_tokens = {False: None, True: None}

    vf_iter = None

    def __init__(self, search_query, max_results = 10):

        if not isinstance(search_query, str):
            raise ValueError("Expected str for 1st parameter (search_query).")
        if not isinstance(max_results, int):
            raise ValueError("Expected int for 2nd parameter (max_results).")

        self.search_query = search_query
        self.max_results = max_results

    def __search(self, pt=None):

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

        api_fixed_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&fields=items(id%2Ckind%2Csnippet)%2CnextPageToken%2CprevPageToken"
        api_key = "AIzaSyCPOg5HQfHayQH6mRu4m2PMGc3eHd5lllg"

        url = "{0}&key={1}&maxResults={2}&q={3}&pageToken=".format(api_fixed_url, api_key, self.max_results, self.search_query)

        try:
            url += pt
        except TypeError:
            pass

        return requests.get(url).json() #FIXME? something can go wrong here...

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

        self.vf_iter = iter(ctrl + [e + ".mp4" for e in self.visible_files])

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

        return self.visible_files[ os.path.splitext(key)[0] ] #pozbywamy się rozszerzenia, btw.

    def __in__(self, arg):

        """
        Check, if movie of name `arg` is present in the object.

        Parameters
        ----------
        arg : str
            Filename.
        """

        arg = os.path.splitext(arg)[0]

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
        files = lambda x: {i['snippet']['title'].replace('/', '\\'): YTStor(i['id']['videoId'], opts={'pub_date': i['snippet']['publishedAt']}) for i in x['items']}

        try:
            if self.adj_tokens[forward] is None: # in case someone would somehow cross boundary.
                forward = None
        except KeyError:
            pass

        try:
            try:
                data = self.avail_files[ self.adj_tokens[forward] ] # maybe data is already available locally.
            except KeyError:
                recv = self.__search( self.adj_tokens[forward] ) # nope, we have to search.
                data = (None, files(recv)) # little format unification.
                                                                                                 
        except KeyError: # wrong index in adj_tokens

            if forward is None:
                recv = self.__search()
                data = (None, files(recv)) # same here
            else:
                raise ValueError("Valid values for forward are True, False or None (default).")

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
