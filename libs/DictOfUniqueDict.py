#!/usr/bin/env python3
# -*- coding: utf-8 -*

# Author: Tomáš Volf, ivolf(at)fit.vutbr.cz

from libs.UniqueDict import *

class DictOfUniqueDict(dict):
    def __missing__(self, key):
        self[key] = UniqueDict()
        return self[key]
