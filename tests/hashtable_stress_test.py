import struct
import random

import pytest

from borghash import HashTable


def H(x, y):
    """
    Create a 256bit key - x will determine the first 32 bits, y will determine the last 32bit.
    As our HashTable computes the ht index from first 32 bits, same x will give same ht index (a collision).
    """
    return struct.pack(">IIIIIIII", x, 0, 0, 0, 0, 0, 0, y)  # BE is easier to read.


@pytest.fixture
def ht():
    # 256bit keys, 32bit values
    return HashTable(key_size=32, value_size=4)


def check(ht, pydict, destructive=False):
    """check if ht has same contents as pydict"""
    assert len(ht) == len(pydict)
    assert dict(ht.items()) == pydict
    for key, value in pydict.items():
        assert ht[key] == value
    if destructive:
        items = list(pydict.items())
        random.shuffle(items)
        for key, value in items:
            del ht[key]
        assert len(ht) == 0


def test_few_collisions_stress(ht):
    pydict = {}
    for h in range(10000):
        key = H(h, h)  # few collisions
        value = key[-4:]
        ht[key] = value
        pydict[key] = value
    check(ht, pydict, destructive=True)


def test_many_collisions_stress(ht):
    pydict = {}
    for h in range(10000):
        key = H(0, h)  # everything collides
        value = key[-4:]
        ht[key] = value
        pydict[key] = value
    check(ht, pydict, destructive=True)


@pytest.mark.parametrize("delete_threshold", [0, 10, 100, 1000, 10000])
def test_ht_vs_dict_stress(ht, delete_threshold):
    SET, GET, DELETE = 0, 1, 2
    UINT32_MAX = 2 ** 32 - 1

    def random_operations(ht, pydict):
        def new_random_keys(count):
            keys = set()
            while len(keys) < count:
                x = random.randint(0, UINT32_MAX)
                key = H(x, x)  # few collisions
                keys.add(key)
            return keys

        def some_existing_keys(count):
            all_keys = list(pydict.keys())
            return random.sample(all_keys, min(len(all_keys), count))

        count = random.randint(1, 20)
        operation = random.choice([SET, GET, DELETE] if len(pydict) > delete_threshold else [SET, GET])
        if operation == SET:
            for key in new_random_keys(count):
                value = key[:4]
                ht[key] = value
                pydict[key] = value
        else:
            for key in some_existing_keys(count):
                if operation == GET:
                    assert ht[key] == pydict[key]
                elif operation == DELETE:
                    del ht[key]
                    del pydict[key]

    pydict = {}
    for _ in range(10000):
        random_operations(ht, pydict)
        check(ht, pydict, destructive=False)
    check(ht, pydict, destructive=True)
