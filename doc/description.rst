Everything can be a file - program behaviour description
********************************************************

This software does not provide any player nor browser. Instead, it provides file interface for already existing programs. Thanks to that, using a simple filesystem operations a user is able to search, play or copy movies on a hard disk using her favourite tools.
Mounting YTFS in any empty directory is all it takes.

Searching
=========

YTFS, with one exception, is a read-only filesystem. The exception is permission to create, delete and rename subdirectories in the main directory. User is not allowed to create or rename files.


By creating a directory (`mkdir`) of given name, user tells YTFS to perform search of this name in YouTube and to put results in this directory. For example, creation of directory named *python* will cause YTFS to put movies which are the results of searching *python* in this directory. One can create many directories like this.

Directory renaming is equivalent to old named directory removal and creation of new named directory. This functionality is implemented due to a fact, that many file managers gives default name to newly created directories (e.g. `New Folder`) which would render YTFS even unusable, if there was no possibility of renaming it.

Example::

    larry@localhost /tmp/ytfs $ mkdir python
    larry@localhost /tmp/ytfs $ cd python
    larry@localhost /tmp/ytfs/python $ ls
     next                                                            Python Attack Compilation 01.mp4
    2 Leopards VS 1 Huge Python.mp4                                  Python Programming.mp4
    A hands-on introduction to Python for beginning programmers.mp4  Python The Dominator! The Ultimate Final Showdown! || Let's Play Terraria 1.2.4 [Episode 50].mp4
    Google Python Class Day 1 Part 1.mp4                             World's Deadliest - Python Eats Antelope.mp4
    How to Learn Python in Five Minutes - Daniel Moniz.mp4           Zero to Hero with Python.mp4
    Indigo Snake Eats Python 01 Stock Footage.mp4

    larry@localhost /tmp/ytfs/python $ cd .. && mv python banana
    larry@localhost /tmp/ytfs $ ls banana/
     next                                                      Minions - Banana! Funny Movie!.mp4                                                         Spider bursts out of a Banana.mp4
    Banana Minion Dance Tribute by Rejuvenate Dance Crew.mp4   Minions - Cow Cup , The Stars are Brighter , Evil Minion Animation Test , Banana song.mp4  Sprite & Banana Challenge.mp4
    Despicable Me 2 | Minions Banana Song (2013) SNSD TTS.mp4  Minions in Gym with Banana!.mp4                                                            [VineClassics] Vinny - Super Banana Effect.mp4
    Minions - Banana 14:20 mins.mp4                            RECHEADOR DE BANANA + α | BIZARRICES DO JAPÃO.mp4

Besides files that are search results, *next* and *prev* (both start with space character!) may appear. Those are executable control files, whose execution will load next or previous search results into directory.

Directory removal will clean given search and will delete downloaded data.

Movies playback
===============

Neither directories created by a user, nor files that appeared in them, does not physically exist on computer's hard drive. We can therefore call them virtual. In practise, they are only a kind of interface to multimedia data from YouTube.

Read operation does not simply read data from hard disk, but first it causes download (if needed), saves it in a buffer and then it returns it to the process that requested for it. Majority of this data is kept in RAM.

Thereby, all multimedia files from YouTube can be accessed (read-only) by any software of one's choice, e.g. ``mplayer`` or ``cp``.
