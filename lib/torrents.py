"""
Module for handling Torrents in BitTorrent.

This module defines classes and utilities for working with Torrents,
including the Torrent class representing the torrent meta-data within
a .torrent file, and the TorrentFile class representing an individual file
within a torrent.

Classes:
    - Torrent: Represents the torrent meta-data within a .torrent file.
    - TorrentFile: Represents an individual file within a torrent.

This module also relies on the 'bencoding' module for handling Bencoded data.

Usage:
    To use this module, create instances of the Torrent class by providing
    the path to a .torrent file. The Torrent class provides access to various
    properties and methods for working with torrent meta-data.

Example:
    from torrents import Torrent

    # Load a torrent file
    torrent = Torrent('example.torrent')

    # Access torrent properties
    print(torrent.announce)
    print(torrent.piece_length)
    print(torrent.total_size)

    # Iterate over individual files in the torrent
    for file in torrent.files:
        print(file.name, file.length)
"""
from hashlib import sha1
from . import bencoding


class TorrentFile:
    """
    Represents an individual file within a torrent.
    """

    def __init__(self, name: str, length: int):
        """
        Initializes a TorrentFile instance.

        :param name: The name of the file.
        :param length: The length of the file in bytes.
        """
        self.name = name
        self.length = length


class Torrent:
    """
    Represents the torrent meta-data that is kept within a .torrent file. It is
    basically just a wrapper around the bencoded data with utility functions.

    This class does not contain any session state as part of the download.
    """

    def __init__(self, filename: str):
        """
        Initializes a Torrent instance.

        :param filename: The path to the .torrent file.
        """
        self.filename = filename
        self.files = []

        with open(self.filename, "rb") as f:
            meta_info = f.read()
            self.meta_info = bencoding.Decoder(meta_info).decode()
            info = bencoding.Encoder(self.meta_info[b"info"]).encode()
            self.info_hash = sha1(info).digest()
            self._identify_files()

    def _identify_files(self):
        """
        Identifies the files included in this torrent.
        """
        if self.multi_file:
            raise RuntimeError("Multi-file torrents are not supported!")
        self.files.append(
            TorrentFile(
                self.meta_info[b"info"][b"name"].decode("utf-8"),
                self.meta_info[b"info"][b"length"],
            )
        )

    @property
    def announce(self) -> str:
        """
        The announce URL to the tracker.

        :return: The announce URL.
        """
        return self.meta_info[b"announce"].decode("utf-8")

    @property
    def multi_file(self) -> bool:
        """
        Does this torrent contain multiple files?

        :return: True if the torrent is multi-file, False otherwise.
        """
        return b"files" in self.meta_info[b"info"]

    @property
    def piece_length(self) -> int:
        """
        Get the length in bytes for each piece.

        :return: The length of each piece in bytes.
        """
        return self.meta_info[b"info"][b"piece length"]

    @property
    def total_size(self) -> int:
        """
        The total size (in bytes) for all the files in this torrent.

        For a single file torrent, this is the only file. For a multi-file torrent,
        this is the sum of all files.

        :return: The total size (in bytes) for this torrent's data.
        """
        if self.multi_file:
            raise RuntimeError("Multi-file torrents are not supported!")
        return self.files[0].length

    @property
    def pieces(self):
        """
        Get the SHA1 hash of each piece in the torrent.

        :return: A list of SHA1 hash values for each piece.
        """
        data = self.meta_info[b"info"][b"pieces"]
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset : offset + 20])
            offset += 20
        return pieces

    @property
    def output_file(self) -> str:
        """
        Get the output file name from the torrent.

        :return: The output file name.
        """
        return self.meta_info[b"info"][b"name"].decode("utf-8")

    def __str__(self):
        """
        Return a string representation of the Torrent.

        :return: A string representation of the Torrent.
        """
        return (
            "Filename: {0}\n"
            "File length: {1}\n"
            "Announce URL: {2}\n"
            "Hash: {3}".format(
                self.meta_info[b"info"][b"name"],
                self.meta_info[b"info"][b"length"],
                self.meta_info[b"announce"],
                self.info_hash,
            )
        )
