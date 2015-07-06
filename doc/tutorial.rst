Short manual
************

YTFS mounting
=============

To mount YTFS in a chosen directory, one should execute ``ytfs.py`` and provide path to empty directory as argument.

Avalaible options:

|   **-a** : Download audio (default)
|   **-v** : Download video
|   **-r** : RickRoll flag

.. important:: YTFS choses best quality available. Format selection will be implemented in the future.

Flags can be used simultaneously, which will cause download of video and audio. In such case, before read from a file all data will be obtained, then audio and video will be merged. When only audio or only video is selected, then download is performed dynamically.

.. warning:: Some programs may have problems with opening full files with video and audio. They can fail after necessity of waiting for a long time after ``open`` call.

Example (when working directory contains ``ytfs.py``)::

    larry@localhost ~/ytfs $ ./ytfs.py -v /tmp/youtube-dir

YTFS will mounted in /tmp/youtube-dir. Only video data will be downloaded (no sound).

.. hint:: If an error (which is not an Python interpreter error) occurs, e.g. ``fusermount: failed to open /etc/fuse.conf: Permission denied``, then YTFS is probably mounted correctly and can be used with no problems.

Searching
=========

To search for movies in YouTube, in a directory where YTFS is mounted (in previous example /tmp/youtube-dir) one should create a subdirectory. Its name will be a search query.

Example::

    larry@localhost /tmp/youtube-dir $ mkdir orange

New search can be performed by renaming a directory which already exists. Previous search results and downloaded data will be lost.

It is possible to remove searches by ``rmdir`` or ``rm -r``.

Example::

    larry@localhost /tmp/youtube-dir $ mkdir kasztana
    larry@localhost /tmp/youtube-dir $ mv kasztana banana
    larry@localhost /tmp/youtube-dir $ rmdir banana

Navigate between search pages
-----------------------------

In a directory, only 10 results are shown. To navigate between search pages one can use following control files:

.. line-block::
    **next** : Load next 10 results.
    **prev** : Load previous 10 results.

Pliki sterujące nie będą obecne w katalogu, jeżeli nie ma możliwości wczytania następnych lub poprzednich wyników.
Control files won't be present in a directory, if it's impossible to load next or previous results.

To switch between pages, execute *next* or *prev*::

    larry@localhost /tmp/youtube-dir/orange $ ./\ next
    larry@localhost /tmp/youtube-dir/orange $ ./\ prev

.. ATTENTION::

   *next* and *prev* file names start with a space character!

Search results usage
====================

Playback
--------

To play a file, one should open it with a multimedia player of her choice.

Downloading on a hard drive
---------------------------

To download a movie, just copy file, e.g. with ``cp`` command or with file manager on a disk.

Example::

    larry@localhost /tmp/youtube-dir/orange $ cp The\ Annoying\ Orange.mp4 ~/

YTFS unmounting
===============

To unmount YTFS from a directory where it was mounted (e.g. /tmp/youtube-dir), make sure that no process uses any file from this directory, then use ``fusermount -u`` command or use a file manager.

Example::

    larry@localhost /tmp $ fusermount -u youtube-dir/
