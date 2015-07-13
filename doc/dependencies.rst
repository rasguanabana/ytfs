Dependencies and third-party software
*************************************

Python 3.4
----------

YTFS was written in `Python 3.4 <https://www.python.org>`_ and this version, or newer, is required to run this program.

FUSE
----

File system was based on `FUSE <http://fuse.sourceforge.net>`_ (Filesystem in Userspace) library. To be able to run YTFS, operating system needs suitable module and libraries.

Python library for FUSE used in YTFS is `fusepy <https://github.com/terencehonles/fusepy>`_ (running ``2to3`` might be necessary). 

YTFS was tested under Linux (``fuse`` module) and OS X (``osxfuse`` module) platforms. In general, it's stable on CLI. Graphical file managers may have some problems with browsing or providing previews.

Only systems where ``fuse`` driver (or any compatible) is available are supported.

youtube-dl
----------

`Youtube-dl <https://rg3.github.io/youtube-dl/>`_ is a program and a Python module wich is capable of downloading movies from many multimedia services, especially from YouTube.

In YTFS used for obtaining direct links to multimedia files and for merging audio and video into one video file.

This dependency most probably will be dropped in the future.

FFmpeg/Libav
------------

`FFmpeg <https://www.ffmpeg.org>`_ or `Libav <https://libav.org>`_ are used for audio and video merging. Required, when YTFS is mounted for downloading video **and** audio.

Requests
--------

`Requests <http://docs.python-requests.org>`_ library is used for data downloading in possibly most simple and readable manner.
