"""Hash table with linked list for entries with same hash."""

# Copyright (c) 2025, ABB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with
# or without modification, are permitted provided that
# the following conditions are met:
#
#   * Redistributions of source code must retain the
#     above copyright notice, this list of conditions
#     and the following disclaimer.
#   * Redistributions in binary form must reproduce the
#     above copyright notice, this list of conditions
#     and the following disclaimer in the documentation
#     and/or other materials provided with the
#     distribution.
#   * Neither the name of ABB nor the names of its
#     contributors may be used to endorse or promote
#     products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import hashlib
from typing import Any

from bt_learning.gp import logplot


# pylint: disable=too-few-public-methods
class Node:
    """Node data structure - essentially a LinkedList node."""

    def __init__(self, key: str, value: Any, value2=None, value3=None, value4=None, value5=None):
        self.key = key
        self.value = [value]
        self.value2 = [value2]
        self.value3 = [value3]
        self.value4 = [value4]
        self.value5 = [value5]
        self.next = None

    def __eq__(self, other: 'Node') -> bool:
        if not isinstance(other, Node):
            return False
        equal = self.key == other.key and self.value == other.value \
            and self.value2 == other.value2 and self.value3 == other.value3 and self.value4 == other.value4 \
            and self.value5 == other.value5
        if equal:
            if self.next is not None or other.next is not None:
                if self.next is None or other.next is None:
                    equal = False
                else:
                    equal = self.next == other.next
        return equal


class HashTable:
    """Main hash table / database class."""

    def __init__(self, size: int = 100000, log_name: str = 'tests/1', file_name: str = '/hash_log.txt'):
        """Initialize hash table to fixed size."""
        self.size = size
        self.buckets = [None]*self.size
        self.n_values = 0
        self.n_steps = 0
        self.log_name = log_name
        self.file_name = file_name

    def __eq__(self, other: 'HashTable') -> bool:
        if not isinstance(other, HashTable):
            return False

        equal = True
        for i in range(self.size):
            if self.buckets[i] != other.buckets[i]:
                equal = False
                break
        return equal

    def __hash(self, key: str) -> int:
        """
        Generate a hash for a given key.

        Args
        ----
            key: the string key

        Returns
        -------
            hash: hashcode generated from the key

        """
        new_hash = hashlib.md5()
        new_hash.update(key.encode('utf-8'))
        hashcode = new_hash.hexdigest()
        hashcode = int(hashcode, 16)
        return hashcode % self.size

    def insert(self, key: list, value: Any) -> None:
        """
        Insert a key - value pair to the hash table.

        Args:
        ----
            key: list
            value: anything

        """
        value2 = 0
        value3 = 0
        value4 = 0
        value5 = 0
        if isinstance(value, tuple):
            if len(value) >= 3:
                self.n_steps += value[-1]

            if len(value) >= 2:
                value2 = value[1]
            if len(value) >= 4:
                value3 = value[2]
            if len(value) >= 5:
                value4 = value[3]
            if len(value) >= 6:
                value5 = value[4]
            if len(value) >= 1:
                value = value[0]
        else:
            value2 = value
            value3 = value
            value4 = value
            value5 = value

        string_key = to_string(key)
        index = self.__hash(string_key)
        node = self.buckets[index]
        if node is None:
            self.buckets[index] = Node(string_key, value, value2, value3, value4, value5)
        else:
            done = False
            while not done:
                if node.key == string_key:
                    node.value.append(value)
                    node.value2.append(value2)
                    node.value3.append(value3)
                    node.value4.append(value4)
                    node.value5.append(value5)
                    done = True
                elif node.next is None:
                    node.next = Node(string_key, value, value2, value3, value4, value5)
                    done = True
                else:
                    node = node.next
        self.n_values += 1

    def find(self, key: list) -> Any:
        """
        Find a data value based on key.

        Args
        ----
            key: key in the hash-table

        Returns
        -------
            value, value2: values stored under "key" or None if not found
        """
        string_key = to_string(key)
        index = self.__hash(string_key)
        node = self.buckets[index]
        while node is not None and node.key != string_key:
            node = node.next

        if node is None:
            return None

        return node.value, node.value2, node.value3, node.value4, node.value5

    def load(self) -> None:
        """Load hash table information."""
        with open(
                logplot.get_log_folder(self.log_name) + self.file_name,
                'r',
                encoding='utf-8'
             ) as f:
            lines = f.read().splitlines()

            for i, line in enumerate(lines):
                individual = line
                individual = individual[5:].split(', value: ')
                key = individual[0]
                individual = individual[1].split(', value2: ')
                individual2 = individual[1].split(', value3: ')
                individual3 = individual2[1].split(', value4: ')
                individual4 = individual3[1].split(', value5: ')
                individual5 = individual4[1].split(', count: ')

                values = individual[0][1:-1].split(', ')  # Remove brackets and split multiples
                values2 = individual2[0][1:-1].split(', ')  # Remove brackets and split multiples
                values3 = individual3[0][1:-1].split(', ')  # Remove brackets and split multiples
                values4 = individual4[0][1:-1].split(', ')  # Remove brackets and split multiples
                values5 = individual5[0][1:-1].split(', ')  # Remove brackets and split multiples
                for i, value in enumerate(values):
                    self.insert(key, (float(value), float(values2[i]), float(values3[i]), float(values4[i]), float(values5[i]), 0))

    def write_table(self):
        """Write table contents to a file."""
        with open(
                logplot.get_log_folder(self.log_name) + self.file_name,
                'w',
                encoding='utf-8'
             ) as f:
            for node in filter(lambda x: x is not None, self.buckets):
                while node is not None:
                    f.writelines(
                        'key: ' + str(node.key) +
                        ', value: ' + str(node.value) +
                        ', value2: ' + str(node.value2) +
                        ', value3: ' + str(node.value3) +
                        ', value4: ' + str(node.value4) +
                        ', value5: ' + str(node.value5) +
                        ', count: ' + str(len(node.value)) + '\n'
                    )
                    node = node.next
        f.close()

    def set_n_steps(self, n_steps):
        """ Sets n_steps from outside """
        self.n_steps = n_steps


def to_string(key: Any) -> str:
    """Convert a key to string."""
    if isinstance(key, str):
        return key
    try:
        string = ', '.join(str(e) for e in key)
    except TypeError:
        string = str(key)
    return string
