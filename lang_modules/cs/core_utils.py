#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file core_utils.py
# @brief cs specific core utilities
#
# contains:
# - is_entity function - non entity function for page identification
# - general functions for all cs entities (del_redundant_text, assign_coordinates, ...)
#
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re, requests
from debugger import Debugger as debug

WIKI_API_URL = "https://cs.wikipedia.org/w/api.php"
WIKI_API_PARAMS_BASE = {
	"action": "query",
	"format": "json",
}

class CoreUtils:
	##
	# @brief function used in wiki_extract.py for for page identification
	@staticmethod
	def is_entity(title):
		# speciální stránky Wikipedie nepojednávají o entitách
		if title.startswith(
			(
				"wikipedie:",
				"redaktor:",
				"soubor:",
				"mediawiki:",
				"šablona:",
				"pomoc:",
				"kategorie:",
				"speciální:",
				"portál:",
				"modul:",
				"seznam",
				"geografie",
				"společenstvo",
			)
		):
			return False

		# stránky pro data (datumy) nepojednávají o entitách
		if re.search(r"^\d{1,2}\. [^\W\d_]+$", title):
			return False

		# ostatní stránky mohou pojednávat o entitách
		return True

	##
	# @brief Odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje.
	# @param text - text, který má být upraven (str)
	# @param multiple_separator - znak oddělující více řádků
	# @param clear_name_links - odstraňuje odkazy z názvů
	# @return Upravený text. (str)
	@staticmethod
	def del_redundant_text(text, multiple_separator="|", langmap=dict()):
		#        if clear_name_links:
		#            clean_text = re.sub(r"(|\s*.*?název\s*=\s*(?!=)\s*.*?)\[\[[^\]]+\]\]", r"\1", text).strip() # odkaz v názvu zřejmě vede na jinou entitu (u jmen často odkazem napsán jazyk názvu)
		#        else:
		link_lang = re.search(r"\[\[(.*?)(?:\|.*?)?\]\]\s*(<br(?: ?/)?>)?", text)
		if link_lang and link_lang.group(1):
			txt_lang = link_lang.group(1).lower()
			if txt_lang in langmap:
				text = text.replace(
					link_lang.group(0), "{{{{Vjazyce|{}}}}} ".format(langmap[txt_lang])
				)
		clean_text = re.sub(
			r"\[\[[^\]|]+\|([^\]|]+)\]\]", r"\1", text
		)  # [[Sth (sth)|Sth]] -> Sth
		clean_text = re.sub(r"\[\[([^]]+)\]\]", r"\1", clean_text)  # [[Sth]] -> Sth
		clean_text = re.sub(r"'{2,}(.+?)'{2,}", r"\1", clean_text)  # '''Sth''' -> Sth
		clean_text = re.sub(
			r"\s*</?small>\s*", " ", clean_text
		)  # <small>sth</small> -> sth
		#        clean_text = re.sub(r"\s*<br(?: ?/)?>\s*", ", ", clean_text)  # sth<br />sth -> sth, sth
		clean_text = re.sub(
			r"\s*<br(?: ?/)?>\s*", multiple_separator, clean_text
		)  # sth<br />sth -> sth, sth (sth-> sth | sth)
		clean_text = re.sub(
			r"\s*{{small\|([^}]+)}}\s*", r" \1", clean_text
		)  # {{small|sth}} -> sth
		clean_text = re.sub(
			r"\s*{{nowrap\|([^}]+)}}\s*", r" \1", clean_text, flags=re.I
		)  # {{nowrap|sth}} -> sth
		clean_text = re.sub(
			r"\s*{{(?:(?:doplňte|doplnit|chybí) zdroj|zdroj\?|fakt[^}]*)}}\s*",
			"",
			clean_text,
			flags=re.I,
		)
		clean_text = clean_text.replace("{{--}}", "–")
		clean_text = clean_text.replace("{{break}}", ", ")
		clean_text = re.sub(r"\s*(?:{{•}}|•)\s*", ", ", clean_text)
		clean_text = clean_text.replace("&nbsp;", " ").replace("\xa0", " ")

		return clean_text

	##
	# @brief extracts coordinates - tries to extract from infoboxes queries wikipedia if unsuccessful
	# @return tuple with string coordinates 
	@classmethod
	def assign_coordinates(cls, entity):
		latitude = ""
		longitude = ""

		# zeměpisná šířka
		keys = ["zeměpisná šířka", "zeměpisná_šířka"]
		for key in keys:
			if key in entity.infobox_data and entity.infobox_data[key]:
				value = entity.infobox_data[key]
				latitude = cls.get_latitude(cls.del_redundant_text(value))
				break

		# zeměpisná výška
		keys = ["zeměpisná výška", "zeměpisná_výška"]
		for key in keys:
			if key in entity.infobox_data and entity.infobox_data[key]:
				value = entity.infobox_data[key]
				longitude = cls.get_longitude(cls.del_redundant_text(value))
				break

		if latitude and longitude:
			return (latitude, longitude)
		else:
			return cls.get_wiki_api_location(entity.title)

	##
	# @brief queries wikipedia for coordinates based on title
	# @param title page title to query
	# @return tuple with string coordinates 
	@staticmethod
	def get_wiki_api_location(title):
		wiki_api_params = WIKI_API_PARAMS_BASE.copy()
		wiki_api_params["prop"] = "coordinates"
		wiki_api_params["titles"] = title
		try:
			r = requests.get(WIKI_API_URL, params=wiki_api_params)
			pages = r.json()["query"]["pages"]
			first_page = next(iter(pages))
			if first_page != "-1":
				latitude = pages[first_page]["coordinates"][0]["lat"]
				longitude = pages[first_page]["coordinates"][0]["lon"]
				return (str(latitude), str(longitude))
			return ("", "")
		except Exception as e:
			return ("", "")

	##
	# @brief Převádí zeměpisnou šířku geografické entity do jednotného formátu.
	# @param latitude - zeměpisná šířka geografické entity (str)
	@staticmethod
	def get_latitude(latitude):
		latitude = re.sub(r"\(.*?\)", "", latitude)
		latitude = re.sub(r"\[.*?\]", "", latitude)
		latitude = re.sub(r"<.*?>", "", latitude)
		latitude = re.sub(r"{{.*?}}", "", latitude).replace("{", "").replace("}", "")
		latitude = re.sub(r"(?<=\d)\s(?=\d)", "", latitude).strip()
		latitude = re.sub(r"(?<=\d)\.(?=\d)", ",", latitude)
		latitude = re.sub(r"^[^\d-]*(?=\d)", "", latitude)
		latitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", latitude)
		latitude = "" if not re.search(r"\d", latitude) else latitude

		return latitude

	##
	# @brief Převádí zeměpisnou délku geografické entity do jednotného formátu.
	# @param longitude - zeměpisná délka geografické entity (str)
	@staticmethod
	def get_longitude(longitude):
		longitude = re.sub(r"\(.*?\)", "", longitude)
		longitude = re.sub(r"\[.*?\]", "", longitude)
		longitude = re.sub(r"<.*?>", "", longitude)
		longitude = re.sub(r"{{.*?}}", "", longitude).replace("{", "").replace("}", "")
		longitude = re.sub(r"(?<=\d)\s(?=\d)", "", longitude).strip()
		longitude = re.sub(r"(?<=\d)\.(?=\d)", ",", longitude)
		longitude = re.sub(r"^[^\d-]*(?=\d)", "", longitude)
		longitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", longitude)
		longitude = "" if not re.search(r"\d", longitude) else longitude

		return longitude

	##
	# @brief handels coeficients like millions, tousands, ...
	# @param value string with possible coeficient
	# @return int coeficient
	@staticmethod
	def get_coef(value):
		if re.search(r"mil\.|mili[oó]n", value, re.I):
			return 10e6
		if re.search(r"tis\.|tis[ií]c", value, re.I):
			return 10e3
		return 1

	##
	# @brief assigns continent from the infobox
	# @param waterarea object with entity data
	# @return extracted continent string
	@classmethod
	def assign_continents(cls, waterarea):
		continent = ""
		# světadíl
		key = "světadíl"
		if key in waterarea.infobox_data and waterarea.infobox_data[key]:
			value = waterarea.infobox_data[key]
			continent = cls.get_continent(CoreUtils.del_redundant_text(value))
		return continent
	
	##
	# @brief Převádí světadíl, na kterém se vodní plocha nachází, do jednotného formátu.
	# @param continent - světadíl, na kterém se vodní plocha nachází (str)
	@staticmethod
	def get_continent(continent):
		continent = re.sub(r"\(.*?\)", "", continent)
		continent = re.sub(r"\[.*?\]", "", continent)
		continent = re.sub(r"<.*?>", "", continent)
		continent = re.sub(r"{{.*?}}", "", continent)
		continent = re.sub(r"\s+", " ", continent).strip()
		continent = re.sub(r", ?", "|", continent).replace("/", "|")
		return continent

	##
	# @brief extracts language specific aliases
	# @param entity object with entity data
	# @return array of tules with aliases ([(alias, language abbreviation), (...), ...])
	def specific_aliases(entity):
		# cs specific
		aliases = []

		if not entity.prefix.startswith("person"):
			keys = entity.infobox_data.keys()
			for key in keys:
				match = re.search(r"úřední\snázev\s(\w+)", key)
				if match:
					lang = match.group(1)
					# TODO: cs langmap
					lang_abbr = ""
					alias = entity.infobox_data[key]
					alias = re.sub(r"&nbsp;", " ", alias)
					alias = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", alias)
					alias = re.sub(r"\[\[(.*?)\]\]", r"\1", alias)
					match = re.search(r"\{\{Cizojazyčně\|(.*?)\|(.*?)\}\}", alias, flags=re.I)
					if match:
						lang_abbr = match.group(1)
						alias = match.group(2)
						aliases += [(alias, lang_abbr)]
						break
					alias = re.sub(r"\{\{(malé|small).*?\}\}", "", alias).strip()
					alias = re.sub(r"'{2}", "", alias)
					alias = re.sub(r"[ \t]{2,3}", "|", alias)
					alias = alias.split("|")
					alias = [re.sub(r"\(.*?\)", "", a).strip() for a in alias]
					if lang in entity.langmap:
						lang = entity.langmap[lang]
						aliases += [(a, lang) for a in alias]
						break
					aliases += [(a, None) for a in alias]
					break

		if entity.prefix.startswith("person") and entity.gender == "F":
			if entity.title[-3:] not in ("ová", "ská") and entity.title[-2:] != "tá":
				aliases += [(f"{entity.title}ová", "cs")]

		return aliases
