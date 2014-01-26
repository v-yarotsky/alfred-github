# -*- coding: utf-8 -*-

import itertools

def pluck(lst, arg='name'):
    return map(lambda i: i.get(arg), lst)

def flatten(listOfLists):
    return itertools.chain.from_iterable(listOfLists)


