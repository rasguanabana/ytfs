.. image:: http://i.imgur.com/Wbss2gh.png

*****************************************

**YTFS** - File system which enables you to search and play movies from YouTube as files - with tools of your choice.  
Based on FUSE, written in Python 3.

Dependencies, manual and documentation: `Read the Docs <http://ytfs.readthedocs.org/en/latest/>`_

Installation
============

You can install YTFS with pip::

    $ pip3 install ytfs

You need **Python 3.4** or newer.

.. important:: Only systems where FUSE lib (or compatible) is available are supported. YTFS was tested on Linux, OS X and FreeBSD.

Usage
=====

Here some basics are shown. See `documentation <http://ytfs.readthedocs.org/en/latest/tutorial.html>`_ for more detailed description.

Mount
-----

Mount YTFS in an empty directory, for example::

    $ mkdir youtube
    $ ytfs youtube

Search
------

Enter the directory where YTFS is mounted and create a directory whose name is your search query. You can use GUI or CLI (note that the latter is most stable). If you like command line::

    $ cd youtube
    $ mkdir "rick astley"

Search results will appear in the directory you have created.

You can narrow your search to a specific channel::

    $ mkdir "foo bar baz channel:foochannel"

Other additional parameters like ``before:``, ``after:`` or ``max:`` are available. See `docs <http://ytfs.readthedocs.org/en/latest/tutorial.html#advanced-search-parameters>`_ for details.

To navigate between search pages use ``next`` and ``prev`` scripts in the search directory. Note that they have a space character at the beginning, thereby in most shells/file managers they should be alphabetically first::

    $ ./\ next
    $ ./\ prev

Playback
--------

You can use search results as regular files. Open them with your favourite player, for example::

    $ mkdir "rick astley"
    $ cd rick\ astley
    $ mplayer "Rick Astley - Never Gonna Give You Up.mp4"

Or you can copy them on your hard drive::

    $ cp "Rick Astley - Never Gonna Give You Up.mp4" ~/youtube-collection/

Unmounting
----------

To unmount, use ``fusermount -u`` and specify the directory where YTFS was mounted::

    $ fusermount -u youtube

Dependencies
============

* FUSE (Python module: `fusepy <https://github.com/terencehonles/fusepy>`_)
* `youtube-dl <https://github.com/rg3/youtube-dl/tree/master/youtube_dl>`_ (this dependency will be droped in the future)
* `Requests <https://github.com/kennethreitz/requests>`_

If you mount YTFS with options to download full videos at heighest quality, then audio and video merging may be needed. In such case FFmpeg or Libav is required.

Contribute!
===========

If you want to suggest a new feature or help with development in any way, please open an issue or contact me via email.

License
=======

MIT (c) Adrian Włosiak
