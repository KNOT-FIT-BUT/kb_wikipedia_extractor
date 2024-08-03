#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_person.py
# @brief contains EntPerson class - entity used for people, artists and groups
#
# @section ent_information entity information
# person and person:fictional:
# - birth_date
# - birth_place
# - death_date
# - death_place 
# - gender
# - jobs
# - nationality
#
# person:artist
# - art_forms
# - urls
#
# person:group - same as person but the values should be arrays separated by "|"
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from debugger import Debugger as debug

from ent_core import EntCore

from lang_modules.en.person_utils import PersonUtils as EnUtils
from lang_modules.cs.person_utils import PersonUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntPerson
# @brief entity used for people, artists and groups
class EntPerson(EntCore):
	##
	# @brief initializes the person entity
	# @param title - page title (entity name) <string>
	# @param prefix - entity type <string>
	# @param link - link to the wikipedia page <string>
	# @param data - extracted entity data (infobox data, categories, ...) <dictionary>
	# @param langmap - language abbreviations <dictionary>
	# @param redirects - redirects to the wikipedia page <array of strings>
	# @param sentence - first sentence of the page <string>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		# vyvolání inicializátoru nadřazené třídy
		super(EntPerson, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)

		# inicializace údajů specifických pro entitu
		self.birth_date = ""
		self.birth_place = ""
		self.death_date = ""
		self.death_place = ""
		self.gender = ""
		self.jobs = ""
		self.nationality = ""
		
		# artist
		self.art_forms = ""
		self.influencers = ""
		self.influencees = ""
		self.ulan_id = ""
		self.urls = ""

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.gender,
			self.birth_date,
			self.birth_place,
			self.death_date,
			self.death_place,
			self.jobs,
			self.nationality
		]
		if self.prefix == "person:artist":
			data += [
				self.art_forms,
				self.influencers,
				self.influencees,
				self.ulan_id,
				self.urls
			]
		return self.serialize("\t".join(data))
	
	##
	# @brief tries to assign entity information (calls the appropriate functions)
	#
	# this function is getting called from the main script after identification
	def assign_values(self, lang):
		self.prefix = utils[lang].assign_prefix(self)
		self.birth_date, self.death_date = utils[lang].assign_dates(self)
		self.assign_places()
		self.assign_gender()
		self.assign_jobs()
		self.assign_nationality()

		self.extract_text()

		# artist
		if self.prefix == "person:artist":
			self.assign_art_forms()
			self.assign_urls()

		if self.prefix == "person:group":
			self.extract_group_aliases()
		else:
			self.extract_aliases()

	##
	# @brief extracts person aliases (excluding group aliases)
	def extract_aliases(self):
		sentence = self.first_sentence
		if not sentence:
			return

		self.core_utils.specific_aliases(self)

		# '''name (name2) surname''' -> name surname, name2 surname
		# '''name "name2" surname''' -> name surname, name2 surname
		patterns = [			
			r"^'''([^,\(]*?)\(([^\(]*?)\)\s*[^\w]*?([^']+)(?<![\s\"])'''",
			r"'''([^\(]*?)\"(.*?)\"\s.*?([^']+)'''"
		]
		for p in patterns:
			match = re.search(p, sentence)		
			if match:
				start, end = match.span()
				matches = [group for group in match.groups()]
				matches = [re.sub(r"(?:někdy|nebo)?\s*(?:také|též|či|alias|or)", "", m) for m in matches]
				matches = [re.sub(r"\(|\)", "", m) for m in matches]
				matches = [m.replace("'", "").strip() for m in matches]
				if len(matches) == 3:
					al_a = f"{matches[0]} {matches[2]}"
					al_b = f"{matches[1]} {matches[2]}"
					self.aliases[al_a] = self.get_alias_properties(None, self.lang)
					self.aliases[al_b] = self.get_alias_properties(None, self.lang)
				sentence = sentence[:start] + " ".join(matches) + sentence[end:]

		# '''name''' '''surname''' -> '''name surname'''
		sentence = re.sub(r"'{3}\s*'{3}", " ", sentence)
		
		# surnames of women
		match = re.search(r"\{\{nee\|(.*?)\}\}", sentence)
		if match:
			start, end = match.span()
			surname = match.group(1)
			surname = surname.replace("'", "")
			name = self.title.split(" ")
			name.pop()
			name = " ".join(name)
			alias = f"{name} {surname}"
			self.aliases[alias] = self.get_alias_properties(None, None)
			sentence = sentence[:start] + surname + sentence[end:]

		matches = re.findall(r"'{3}(.*?)'{3}", sentence)
		for match in matches:
			alias = match
			alias = re.sub(r"\(|\)|;", "", alias)
			alias = re.sub(r"'{2,}", "", alias)
			self.aliases[alias] = self.get_alias_properties(None, None)

		sentence = re.sub(r"'{3,}", "", sentence)
		self.first_sentence = sentence

	##
	# @brief extracts group aliases
	#
	# NOT UNIFIED - cs version is not extracting group entities yet
	def extract_group_aliases(self):
		sentence = self.first_sentence
		aliases = []

		match = re.search(r"saints (\w+) and (\w+)", self.title)
		if match:
			aliases.append(f"Saint {match.group(1)}")
			aliases.append(f"Saint {match.group(2)}")

		# '''name''' '''name2''' -> '''name name2'''
		sentence = re.sub(r"'{3}\s*'{3}", " ", sentence)
		sentence = re.sub(r"\(('{3}.*?)'{3}\)\s*'{3}", r"\1 ", sentence)

		match = re.findall(r"'{3}(.*?)'{3}", sentence)
		for m in match:
			m = re.sub(r"'{2,}", "", m)
			if m.lower() != self.title.lower():
				match = re.search(r"saints (\w+) and (\w+)", m, flags=re.I)
				if match:
					aliases.append(f"Saint {match.group(1)}")
					aliases.append(f"Saint {match.group(2)}")
					continue
				m = m.split(",")
				for value in m:
					value = re.sub(r"^(and|&)", "", value).strip()
					value = re.sub(r"\s+(and|&)\s+", "|", value).split("|")
					value = [v.replace("\"", "") for v in value if not re.search(r"companions", v, flags=re.I)]
					aliases += value
		
		for a in aliases:
			self.aliases[a] = self.get_alias_properties(None, None)

	##
	# @brief extracts and assigns places from infobox, removes wikipedia formatting
	def assign_places(self):
		def fix_place(place):
			p = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", place, flags=re.I)
			p = re.sub(r"{{flagicon\|(.*?)(?:\|.*?)?}}", r"\1", p, flags=re.I)
			p = re.sub(r"{{(?:malé|small)\|(.*?)}}", r"\1", p, flags=re.I)
			p = re.sub(r"{{nowrap\|(.*?)}}", r"\1", p)
			p = re.sub(r"\[\[(?:file|soubor|image):.*?\]\]", "", p, flags=re.I)
			p = re.sub(r"\{\{.*?\}\}", "", p)
			p = re.sub(r"\[\[[^]]*?\|([^\|]*?)\]\]", r"\1", p)
			p = re.sub(r"\[|\]", "", p)
			p = re.sub(r"\s+", " ", p)
			return p.strip()

		value = self.get_infobox_data(self.keywords["birth_place"])
		if value:
			birth_place = fix_place(value)
			self.birth_place = birth_place

		value = self.get_infobox_data(self.keywords["birth_place"])
		if value:
			death_place = fix_place(value)
			self.death_place = death_place

	##	
	# @brief extracts and assigns gender
	def assign_gender(self):
		# infobox search
		value = self.get_infobox_data(self.keywords["gender"])
		if value:
			value = value.lower().strip()
			value = re.sub(r"\(.*?\)", "", value).strip()			
			if value in self.keywords["male"]:
				self.gender = "M"
			elif value in self.keywords["female"]:
				self.gender = "F"
			else:
				debug.log_message(f"Error: invalid gender - {value}")

		# look for keywords in categories
		if not self.gender and self.prefix != "person:fictional":
			for c in self.categories:
				if re.search("|".join(self.keywords["female"]), c.lower()):
					self.gender = "F"
				if re.search("|".join(self.keywords["male"]), c.lower()):
					self.gender = "M"
	
	##
	# @brief extracts and assigns jobs from the infobox
	def assign_jobs(self):
		data = self.get_infobox_data(self.keywords["jobs"])
		if data:
			jobs = []

			# [[...|data]]
			value = re.sub(r"\[\[[^]]*?\|(.+?)\]\]", r"\1", data)
			# [[data]]
			value = re.sub(r"\[\[(.+?)\]\]", r"\1", value)
			# {{nowrap|data}}
			value = re.sub(r"{{nowrap\|([^}]+)}}", r"\1", value, flags=re.I)

			# data (irrelevant data)
			value = re.sub(r"\(.*?\)", "", value).strip()
			# getting rid of wikipedia templates
			value = re.sub(r"\'{2,3}", "", value)
			value = re.sub(r"&nbsp;", " ", value)

			value = value.replace("\n", "").strip()
			# plainlists and flatlists - {{plainlist|*job *job}}
			pattern = r"\{\{(?:(?:indented\s)?plainlist|flatlist)\s*?\|(.*?)\}\}"
			match = re.search(pattern, value, flags=re.I)
			if match:
				array = match.group(1).strip()
				array = [a.strip() for a in array.split("*") if a]
				if len(array):
					jobs += array
					value = re.sub(pattern, "", value, flags=re.I).strip()
			
			# hlists and unbulleted lists - {{hlist|job|job}}
			pattern = r"\{\{(?:hlist|ubl|unbulleted\slist)\s*?\|(.*?)\}\}"
			match = re.search(pattern, value, flags=re.I)
			if match:
				array = match.group(1).strip()
				array = [a.strip() for a in array.split("|") if a]
				if len(array):
					jobs += array
					value = re.sub(pattern, "", value, flags=re.I).strip()

			# data {{unsuported template}}
			value = re.sub(r"\{\{.*?\}\}", "", value).strip()

			match = re.search(r"([;*•])", value)
			if match:
				char = match.group(1)
				array = value.split(char)
				array = [a.strip() for a in array if a]
				jobs += array
			elif value:
				value = value.replace(", and", ",")
				array = value.split(",")
				array = [a.strip() for a in array if a]
				jobs += array

			self.jobs = "|".join(jobs)
	
	##
	# @brief extracts nationality
	def assign_nationality(self):
		nationalities = []

		data = self.get_infobox_data(self.keywords["nationality"])
		if data:
			# remove irrelevant wiki templates
			value = re.sub(r"\{\{(?:citation|flagicon)[^}]*?\}\}", "", data, flags=re.I)
			value = re.sub(r"\[\[(?:image|file|soubor|obrázek):[^]]*?\]\]", "", value, flags=re.I)

			# [[...|data]]
			value = re.sub(r"\[\[[^]]*?\|(.+?)\]\]", r"\1", value)
			# [[data]]
			value = re.sub(r"\[\[(.+?)\]\]", r"\1", value)
			value = re.sub(r"\[|\]", "", value)
			# data (irrelevant data)
			value = re.sub(r"\(.*?\)", "", value).strip()
			
			# use other templates (e.g.: {{flag|...}}, {{USA}})
			value = re.sub(r"\{\{.+?\|(.+?)\}\}", r"\1", value)
			value = re.sub(r"\{\{(.*?)\}\}", r"\1", value)

			value = value.strip()

			value = re.sub(r"\s(?:and|a)\s", ",", value)
			value = re.sub(r"\s{2,}", ",", value)
			match = re.search(r"(/|-|–|,)", value) 
			if match:
				char = match.group(1)
				array = value.split(char)
				array = [a.strip() for a in array if a]
				nationalities += array
			else:
				nationalities.append(value)
			
			self.nationality = "|".join(nationalities)

	##
	# @brief extracts data from the first sentence
	# TODO: extract gender from categories
	def extract_text(self):
		# dates and places
		if self.birth_date or self.death_date or self.birth_place or self.death_place:
			birth_date, death_date, birth_place, death_place = utils[self.lang].extract_dates_and_places(self)
			if not self.birth_date:
				self.birth_date = birth_date
			if not self.death_date:
				self.death_date = death_date
			if not self.birth_place:
				self.birth_place = birth_place
			if not self.death_place:
				self.death_place = death_place

	##
	# @brief extracts and assigns art forms from the infobox
	#
	# NOT UNIFIED - cs version is not extracting artist entities yet
	def assign_art_forms(self):
		keys = ("movement", "field")

		art_forms = ""

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				value = self.infobox_data[key].replace("\n", " ")
				if "''" in value:
					continue
				value = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", value)
				value = re.sub(r"\[|\]", "", value)
				value = re.sub(r"\{\{.*?\}\}", "", value)
				value = value.lower()
			  
				value = [item.strip() for item in value.split(",")]
				
				if len(value) == 1:
					value = value[0]
					value = [item.strip() for item in value.split("/")]
				
				value = "|".join(value)

				if value != "":
					if art_forms == "":
						art_forms = value
					else:
						art_forms += f"|{value}"
		
		self.art_forms = art_forms

	##
	# @brief extracts and assigns urls from the infobox
	#
	# NOT UNIFIED - cs version is not extracting artist entities yet
	def assign_urls(self):
		urls = ""	
		if "website" in self.infobox_data and self.infobox_data["website"] != "":
			value = self.infobox_data["website"]
			value = re.sub(r"\{\{url\|(?:.*?=)?([^\|\}]+).*?\}\}", r"\1", value, flags=re.I)
			value = re.sub(r"\[(.*?)\s.*?\]", r"\1", value)
			urls = value
		self.urls = urls
