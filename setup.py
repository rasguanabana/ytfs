from setuptools import setup
from ytfs import __version__

setup(
    name = 'ytfs',
    version = __version__,
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
    install_requires = ['fusepy', 'youtube_dl', 'requests']
)
