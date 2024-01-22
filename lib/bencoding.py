"""
Module for Bencoding, a data serialization format used in BitTorrent.

Bencoding is a simple data serialization format used in BitTorrent for encoding
various types of data, such as integers, strings, lists, and dictionaries.

This module provides a Decoder class for decoding bencoded data into Python objects
and an Encoder class for encoding Python objects into bencoded data.
"""
from collections import OrderedDict
from typing import Union
from . import TOKEN_DICT, TOKEN_END, TOKEN_INTEGER, TOKEN_LIST, TOKEN_STRING_SEPARATOR


class Decoder:
    """
    Decodes a bencoded sequence of bytes.
    """

    def __init__(self, data: bytes) -> None:
        """
        Initializes the Decoder with the input bencoded data.

        :param data: The bencoded data as bytes.
        :type data: bytes
        """
        if not isinstance(data, bytes):
            raise TypeError('Argument "data" must be of type bytes')
        self._data = data
        self._index = 0

    def decode(self) -> Union[str, int, list, dict, bytes]:
        """
        Decodes the bencoded data and returns the corresponding Python object.

        :return: A Python object representing the bencoded data.
        """
        c = self._peek()
        if c is None:
            raise EOFError("Unexpected end-of-file")
        elif c == TOKEN_INTEGER:
            self._consume()  # The token
            return self._decode_int()
        elif c == TOKEN_LIST:
            self._consume()  # The token
            return self._decode_list()
        elif c == TOKEN_DICT:
            self._consume()  # The token
            return self._decode_dict()
        elif c == TOKEN_END:
            return None
        elif c in b"01234567899":
            return self._decode_string()
        else:
            raise RuntimeError("Invalid token read at {0}".format(str(self._index)))

    def _peek(self) -> Union[bytes, None]:
        """
        Return the next character from the bencoded data or None.
        """
        if self._index + 1 >= len(self._data):
            return None
        return self._data[self._index : self._index + 1]

    def _consume(self) -> bytes:
        """
        Read (and therefore consume) the next character from the data.
        """
        self._index += 1

    def _read(self, length: int) -> bytes:
        """
        Read the `length` number of bytes from data and return the result.

        :param length: The number of bytes to read.
        :type length: int

        :return: The read bytes.
        """
        if self._index + length > len(self._data):
            raise IndexError(
                "Cannot read {0} bytes from current position {1}".format(
                    str(length), str(self._index)
                )
            )
        res = self._data[self._index : self._index + length]
        self._index += length
        return res

    def _read_until(self, token: bytes) -> bytes:
        """
        Read from the bencoded data until the given token is found and return
        the characters read.

        :param token: The token to search for.
        :type token: bytes

        :return: The characters read until the token is found.
        """
        try:
            occurrence = self._data.index(token, self._index)
            result = self._data[self._index : occurrence]
            self._index = occurrence + 1
            return result
        except ValueError:
            raise RuntimeError("Unable to find token {0}".format(str(token)))

    def _decode_int(self) -> int:
        """
        Decode the bencoded integer.

        :return: The decoded integer.
        """
        return int(self._read_until(TOKEN_END))

    def _decode_list(self) -> list:
        """
        Decode the bencoded list.

        :return: The decoded list.
        """
        res = []
        # Recursive decode the content of the list
        while self._data[self._index : self._index + 1] != TOKEN_END:
            res.append(self.decode())
        self._consume()  # The END token
        return res

    def _decode_dict(self) -> dict:
        """
        Decode the bencoded dictionary.

        :return: The decoded dictionary.
        """
        res = OrderedDict()
        while self._data[self._index : self._index + 1] != TOKEN_END:
            key = self.decode()
            obj = self.decode()
            res[key] = obj
        self._consume()  # The END token
        return res

    def _decode_string(self) -> str:
        """
        Decode the bencoded string.

        :return: The decoded string.
        """
        bytes_to_read = int(self._read_until(TOKEN_STRING_SEPARATOR))
        data = self._read(bytes_to_read)
        return data


class Encoder:
    """
    Encodes a python object to a bencoded sequence of bytes.

    Supported python types are:
        - str
        - int
        - list
        - dict
        - bytes

    Any other type will simply be ignored.
    """

    def __init__(self, data: Union[str, int, list, dict, bytes]) -> None:
        """
        Initializes the Encoder with the input Python object.

        :param data (str | int | list | dict | bytes): The Python object to be encoded.
        """
        self._data = data

    def encode(self) -> bytes:
        """
        Encode a python object to a bencoded binary string.

        :return: The bencoded binary data.
        """
        return self.encode_next(self._data)

    def encode_next(self, data: Union[str, int, list, dict, bytes]) -> Union[str, int, list, dict, bytes]:
        """
        Encode the next part of the Python object to a bencoded binary string.

        :param data: The part of the Python object to be encoded.

        :return: The bencoded binary data for the specified part.
        """
        if type(data) == str:
            return self._encode_string(data)
        elif type(data) == int:
            return self._encode_int(data)
        elif type(data) == list:
            return self._encode_list(data)
        elif type(data) == dict or type(data) == OrderedDict:
            return self._encode_dict(data)
        elif type(data) == bytes:
            return self._encode_bytes(data)
        else:
            return None

    def _encode_int(self, value: int) -> bytes:
        """
        Encode an integer to a bencoded binary string.

        :param value: The integer to be encoded.

        :return: The bencoded binary data for the integer.
        """
        return str.encode("i" + str(value) + "e")

    def _encode_string(self, value: str) -> bytes:
        """
        Encode a string to a bencoded binary string.

        :param value: The string to be encoded.

        :return: The bencoded binary data for the string.
        """
        res = str(len(value)) + ":" + value
        return str.encode(res)

    def _encode_bytes(self, value: str) -> bytes:
        """
        Encode bytes to a bencoded binary string.

        :param value: The bytes to be encoded.

        :return: The bencoded binary data for the bytes.
        """
        result = bytearray()
        result += str.encode(str(len(value)))
        result += b":"
        result += value
        return result

    def _encode_list(self, data) -> bytes:
        """
        Encode a list to a bencoded binary string.

        :param data: The list to be encoded.

        :return: The bencoded binary data for the list.
        """
        result = bytearray("l", "utf-8")
        result += b"".join([self.encode_next(item) for item in data])
        result += b"e"
        return result

    def _encode_dict(self, data: dict) -> bytes:
        """
        Encode a dictionary to a bencoded binary string.

        :param data: The dictionary to be encoded.

        :return: The bencoded binary data for the dictionary.
        """
        result = bytearray("d", "utf-8")
        for k, v in data.items():
            key = self.encode_next(k)
            value = self.encode_next(v)
            if key and value:
                result += key
                result += value
            else:
                raise RuntimeError("Bad dict")
        result += b"e"
        return result


