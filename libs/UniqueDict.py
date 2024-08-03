#!/usr/bin/env python3
# -*- coding: utf-8 -*

# Author: Tomáš Volf, ivolf(at)fit.vutbr.cz

KEY_LANG = "lang"
LANG_ORIG = "orig"
LANG_UNKNOWN = "???"


class UniqueDict(dict):
    VALUE_CONFLICTED = "!!!"

    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value if value != "" else None)
        elif self[key] in [None, ""] or (
            key == KEY_LANG and self[key] in [LANG_ORIG, LANG_UNKNOWN]
        ):
            dict.__setitem__(self, key, value)
        elif not value in [None, ""] and self[key] != value:
            if key != KEY_LANG or value not in [LANG_ORIG, LANG_UNKNOWN]:
                # if value not empty and dict[key] is not empty also
                # => CONFLICT of values
                dict.__setitem__(self, key, self.VALUE_CONFLICTED)
            # else: key is KEY_LANG and new language value is LANG_ORIG
            # or LANG_UNKNOWN => OK, may be ignored
        # else (value is empty or dict[key] is equal to value
        # => OK, may be ignored
