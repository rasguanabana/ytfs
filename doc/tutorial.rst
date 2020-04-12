Short manual
************

YTFS mounting
=============

To mount YTFS in a chosen directory, one should execute ``ytfs`` command and provide path to empty directory as argument.

Avalaible options:

.. line-block::
    **-a** : Download audio only.
    **-v** : Download video only.
    **-f** : Specify format as video height, e.g. ``-f 240``.
    **-r** : RickRoll flag.
    **-P** : Load whole data before reading (disables streaming preference). Useful for obtaining heighest video quality.
    **-d** : Debug - run YTFS in foreground.
    **-m** : Obtain metadata. Available values: ``desc`` - descriptions, ``thumb`` - thumbnails. They will appear as a separate files in a search directory. If you want to specify more values than one, separate them with comma, e.g. ``-m desc,thumb``.

You will be able to override those options for individual searches. See :ref:`ov_m_opts`.

.. important:: By default, YTFS provides streamable full movie data. Most probably, it won't be in the highest quality available. For best quality -P flag may be needed.

.. warning:: Some programs may have problems with preloaded files. They can fail after necessity of waiting for a long time after ``open`` call.

Example::

    larry@localhost ~/ytfs $ ytfs -v /tmp/youtube-dir

YTFS will be mounted in /tmp/youtube-dir. Only video data will be downloaded (no sound).

.. hint:: If an error (which is not a Python interpreter error) occurs, e.g. ``fusermount: failed to open /etc/fuse.conf: Permission denied``, then YTFS is probably mounted correctly and can be used with no problems.

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

YouTube Data v3 API Key
=======================

You can specify your own api key for the YouTube Data v3 API using the ``--youtube-api-key`` option or by setting the ``YTFS_YOUTUBE_API_KEY`` environment variable.

Navigate between search pages
-----------------------------

By default, only 10 results are shown in a directory. To navigate between search pages one can use following control files:

.. line-block::
    **next** : Load next results.
    **prev** : Load previous results.

Control files won't be present in a directory, if it's impossible to load next or previous results.

To switch between pages, execute *next* or *prev*::

    larry@localhost /tmp/youtube-dir/orange $ ./\ next
    larry@localhost /tmp/youtube-dir/orange $ ./\ prev

.. ATTENTION::

   *next* and *prev* file names start with a space character!

.. _adv_s_params:

Advanced search parameters
--------------------------

To provide additional search parameters, append, prepend or insert a ``param:value`` string to your search query. If `value` contains spaces, surround it with parentheses: ``param:(foo bar baz)``.

Available parameters:

.. line-block::
    **channel** - Search only for movies that belong to specified channel. If channel isn't found, then this parameter is ignored.
    **max** - Value from 0 to 50. Specify max result number per search "page". Defaults to 10.
    **before** - Search before specified date. Format YYYY-MM-DD, e.g. 2010-10-10.
    **after** - Search after specified date. Format as above.
    **order** - Specify the method that will be used to order resources. Values: `date`, `rating`, `relevance`, `title` and `viewCount`. Default is relevance.

.. note:: If ``channel`` is given, then you can ommit actual search query. Most popular videos of the channel will be returned.

.. important:: Invalid values for ``max``, ``before``, ``after`` parameters will render empty search directory.

Examples::

    larry@localhost /tmp/youtube-dir/ $ mkdir "channel:foobar"
    larry@localhost /tmp/youtube-dir/ $ mkdir "funny cats channel:(funny stuff) max:15"
    larry@localhost /tmp/youtube-dir/ $ mkdir "oranges channel:fruits after:2015-06-01"
    larry@localhost /tmp/youtube-dir/ $ mkdir "channel:snakes python"
    larry@localhost /tmp/youtube-dir/ $ mkdir "foo bar max:1"

.. _ov_m_opts:

Overriding mount options for specific directory
-----------------------------------------------

If you have mounted YTFS with, let's say, with default options, you can override them for a specific search. Append options between brackets (``[``, ``]``) to the directory name. If an option takes a parameter, specify it between parentheses. You don't have to seperate options.

Available options:

.. line-block::
    **a** - Download audio
    **v** - Download video
    **f** - Specify format - takes a parameter.
    **s** - Stream
    **P** - Don't stream (preload)
    **m** - Specify metadata to obtain - can take a parameter. Giving no parameter will disable metadata.

Examples::

    larry@localhost /tmp/youtube-dir/ $ mkdir "foo [a]"                # download audio only.
    larry@localhost /tmp/youtube-dir/ $ mkdir "bar [vP]"               # download video only, don't stream.
    larry@localhost /tmp/youtube-dir/ $ mkdir "baz channel:foo [avs]"  # download audio and video, stream.
    larry@localhost /tmp/youtube-dir/ $ mkdir "foobar [vf(360)s]"      # download video (prefered quality: 360), stream.
    larry@localhost /tmp/youtube-dir/ $ mkdir "foo [m(desc)]"          # obtain descriptions.
    larry@localhost /tmp/youtube-dir/ $ mkdir "foo [m(desc,thumb)]"    # obtain descriptions and thumbnails.
    larry@localhost /tmp/youtube-dir/ $ mkdir "foo [m]"                # don't obtain any metadata.
    larry@localhost /tmp/youtube-dir/ $ mkdir "foo [m()]"              # the same as above.

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
