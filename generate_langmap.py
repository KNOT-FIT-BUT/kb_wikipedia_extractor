#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file generate_langmap.py
# @brief generates langmap if langmap.json was not found
#
# @author created by Jan Kapsa (xkapsa00)
# @date 25.07.2022 

import re
import json
import requests

LANG_TRANSFORMATIONS = {
    "aština": "ašsky",
    "ština": "sky",
    "čtina": "cky",
    "atina": "atinsky",
    "o": "u",
}

##
# @brief generates langmap for the czech language
def generate_cs():
	r = requests.get("https://cs.wikipedia.org/w/index.php?title=Speci%C3%A1ln%C3%AD:Exportovat_str%C3%A1nky&pages=Seznam%20k%C3%B3d%C5%AF%20ISO%20639-2%0A")
	lines = r.text.split("\n")
	
	items = []
	for line in lines:
		if re.search(r"^\|[a-z]{3}", line):
			items.append(line)

	langs = dict()

	for item in items:
		split = item.split("||")

		abb = split[0].strip("|").strip()
		abb = re.sub(r"\{\{.*?\}\}", "", abb)
		abb = abb.split("/")

		ab = split[1].strip()
		ab = re.sub(r"&amp;nbsp;", "", ab)
		if ab:
			for a in abb:
				langs[a] = ab

		abb = abb[-1]

		split[2] = split[2].strip()
		split[2] = re.sub(r"\(.*?\)", "", split[2]).strip()
		if split[2] in ("směs více jazyků", "vyhrazeno pro místní užití", "žádný lingvistický obsah"):
			continue
		split[2] = re.sub(r"\[.*?\|(.*?)\]", r"\1", split[2])
		split[2] = re.sub(r"\[|\]", "", split[2])
		languages = split[2].split(",")
		languages = [l.strip() for l in languages if l]
		for l in languages:
			for key in LANG_TRANSFORMATIONS.keys():
				if re.search(key + r"$", l):
					l = l.replace(key, LANG_TRANSFORMATIONS[key])
					l = l.split()[-1]
					langs[l] = abb
					langs[ab if ab else abb] = l

	with open("json/langmap_cs.json", "w", encoding="utf8") as f:
		json.dump(langs, f, ensure_ascii=False, indent=4)

##
# @brief gets a "List of ISO 639-2 codes" wikipedia page and generates langmap for the english language
def generate_en():
	r = requests.get("https://en.wikipedia.org/w/index.php?title=Special:Export&pages=List_of_ISO_639-2_codes")
	lines = r.text.split("\n")
	items = []
	for line in lines:
		if line.startswith("| {{iso639-2"):
			items.append(line)
	langs = dict()
	for item in items:
		split = item.split("||")
		split[3] = split[3].strip()
		if split[3] != "":
			split[0] = re.sub(r".*{{iso639-2\|(...)(?:-...)?}}.*", r"\1", split[0])
			split[4] = re.sub(r"\[\[.*\|(.*)\]\]", r"\1", split[4])
			split[4] = re.sub(r"\[|\]", "", split[4])
			split[4] = re.sub(r"&nbsp;|&amp;nbsp;", " ", split[4])
			split[4] = re.sub(r",.*$", "", split[4])
			split[4] = re.sub(r"\(.*\)", "", split[4])
			split[4] = split[4].split(";")[0]
			split[4] = split[4].strip().lower()
			langs[split[0]] = split[3]
			langs[split[3]] = split[4]
			langs[split[4]] = split[3]

	with open("json/langmap_en.json", "w", encoding="utf8") as f:
		json.dump(langs, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
	generate_en()
	generate_cs()