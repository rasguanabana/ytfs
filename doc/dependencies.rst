Dependencies and third-party software
*************************************

Python 3.4
----------

YTFS was written in `Python 3.4 <https://www.python.org>`_ and this version, or newer, is required to run this program.

FUSE
----

File system was based on `FUSE <http://fuse.sourceforge.net>`_ (Filesystem in Userspace) library. To be able to run YTFS, operating system needs suitable module and libraries.

* Linux, FreeBSD, OpenSolaris, Minix 3, Android - ``fuse`` (tested only on Linux)
* NetBSD, DragonFLY BSD - ``puffs`` (not tested).
* OS X - ``osxfuse`` (tested, needs some fixes.)
* Windows - ``Dokan``, ``DokanX`` (not tested, probably not working).

YTFS was tested under Linux and OS X platforms, but on OS X there are some problems with ``xattrs``, which prevents reading from file. On Linux YTFS works properly, save some minor issues.

Python library for FUSE used in YTFS is `fusepy <https://github.com/terencehonles/fusepy>`_ (running ``2to3`` might be necessary). 

Due to this dependency, only systems where ``fuse`` driver (or any compatible) is available are supported.

youtube-dl
----------

`Youtube-dl <https://rg3.github.io/youtube-dl/>`_ is a program and a Python module wich is capable of downloading movies from many multimedia services, especially from YouTube.

In YTFS used for obtaining direct links to multimedia files and for merging audio and video into one video file.

FFmpeg/Libav
------------

`FFmpeg <https://www.ffmpeg.org>`_ or `Libav <https://libav.org>`_ are used for audio and video merging. Required, when YTFS is mounted for downloading video **and** audio.

Requests
--------

`Requests <http://docs.python-requests.org>`_ library is used for data downloading in possibly most simple and readable manner.
