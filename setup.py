from setuptools import setup

import re
import ast


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('ytfs/ytfs.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name = 'ytfs',
    version = version,
    description = "YouTube File System",
    long_description = "YTFS - FUSE based file system which enables you to search and play movies from YouTube as files - with tools of your choice.",
    url = "https://github.com/rasguanabana/ytfs",
    author = "Adrian Włosiak",
    author_email = "adwlosiakh@gmail.com",
    license = "MIT",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: System :: Filesystems",
    ],
    keywords = "youtube fuse filesystem",
    packages = ['ytfs'],
    install_requires = ['fusepy', 'youtube_dl', 'requests'],
    entry_points = {'console_scripts': ['ytfs = ytfs.ytfs:main']}
)
