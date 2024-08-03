#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_core.py
# @brief contains EntCore entity - parent core enitity with useful functions
# 
# see class for more information
#
# @section important_functions important functions
# - image and alias extraction
# - date extraction
# - unit conversion
# - latitude and longtitude extraction
#
# @section general_ent_information general entity information
# - ID
# - prefix
# - title
# - aliases
# - redirects
# - description
# - original title
# - images
# - link
#
# description is first sentence extracted from a file passed to the core entity during initialization <br>
# if first sentece is not found in the file it is extracted with the get_first_sentence function <br>
# but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
# 
# @section date_conversion date conversion 
# main function extracting dates is the extract_date function <br>
# other date functions are helper function to the main function and they are not ment to be called
#
# @author created by Jan Kapsa (xkapsa00)
# @date 28.07.2022

from abc import ABCMeta, abstractmethod
import re, random
from hashlib import md5, sha224
import mwparserfromhell as parser

from debugger import Debugger as debug

from lang_modules.en.core_utils import CoreUtils as EnCoreUtils
from lang_modules.cs.core_utils import CoreUtils as CsCoreUtils

from libs.DictOfUniqueDict import DictOfUniqueDict
from libs.UniqueDict import KEY_LANG, LANG_UNKNOWN

KEY_NAMETYPE = "ntype"

utils = {
	"en": EnCoreUtils,
	"cs": CsCoreUtils
}

## 
# @class EntCore
# @brief abstract parent entity
# 
# contains the general information that is shared across all entities and some useful functions
class EntCore(metaclass=ABCMeta):
	# old id generation:
	# this is a bad idea because of multiprocessing 
	# counter = 0

	##
	# @brief initializes the core entity
	# @param title - page title (entity name) <string>
	# @param prefix - entity type <string>
	# @param link - link to the wikipedia page <string>
	# @param data - extracted entity data (infobox data, categories, ...) <dictionary>
	# @param langmap - language abbreviations <dictionary>
	# @param redirects - redirects to the wikipedia page <array of strings>
	# @param sentence - first sentence of the page <string>
	@abstractmethod
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		# old id generation:
		# EntCore.counter += 1
		# self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]

		# general information

		self.eid = sha224(str(random.randint(1, 1000000)).encode("utf-8")).hexdigest()[:10]
		self.prefix = prefix
		self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
		self.aliases = DictOfUniqueDict()
		self.redirects = redirects
		self.description = sentence
		self.original_title = title
		self.images = ""
		self.link = link
		self.langmap = langmap
		self.keywords = keywords

		self.lang = link[8:10]
		self.core_utils = utils[self.lang]

		# extracted data
		self.infobox_data       = data["data"]
		self.infobox_name       = data["name"]
		self.categories         = data["categories"]
		self.first_paragraph    = data["paragraph"]
		self.coords             = data["coords"]
		self.extracted_images   = data["images"]
		
		self.first_sentence = ""
		
		self.extract_images()
		
		self.get_first_sentence()
		self.get_infobox_aliases()
		self.get_native_names()
		self.get_lang_aliases()

	##
	# @brief serializes entity data for output (tsv format)
	# @param ent_data - child entity data that is merged with general data <tsv string>
	# @return tab separated values containing all of entity data <string>
	def serialize(self, ent_data):
		data = "\t".join([
			self.eid,
			self.prefix,
			self.title,
			self.serialize_aliases(),
			"|".join(self.redirects),
			self.description,
			self.original_title,
			self.images,
			self.link,
			ent_data
		]).replace("\n", "")
		return data

	##
	# @brief extracts data from infobox dictionary given an array of keys
	# @return array of data found in the infobox dictionary
	def get_infobox_data(self, keys, return_first=True):
		if isinstance(keys, str):
			keys = [keys]
		data = []
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				if return_first:
					return value
				else:
					data.append(self.infobox_data[key])

		return "" if return_first else data

	##
	# @brief removes wikipedia formatting
	# @param data - string with wikipedia formatting
	# @return string without wikipedia formatting
	@staticmethod
	def remove_templates(data):
		data = re.sub(r"\{\{.*?\}\}", "", data)
		data = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", data)
		data = re.sub(r"\[|\]|'|\(\)", "", data)
		return data

	##
	# @brief extracts and assigns area from infobox
	def assign_area(self):
		def fix_area(value):
			area = re.sub(r"&nbsp;", "", value)
			area = re.sub(r"(?<=\d)\s(?=\d)", "", area)
			area = re.sub(r"\{\{.*\}\}", "", area)
			area = re.sub(r",(?=\d{3})", "", area)
			area = area.replace(",", ".")
			area = re.sub(r"(\d+(?:\.\d+)?)(?:.+|$)", r"\1", area)

			return area.strip()

		# km2
		data = self.get_infobox_data(self.keywords["area_km2"], return_first=False)
		for d in data:
			area = fix_area(d)
			if area:
				return area

		# sq_mi
		data = self.get_infobox_data(self.keywords["area_sqmi"], return_first=False)
		for d in data:
			area = fix_area(d)
			area = self.convert_units(area, "sqmi")
			if area:
				return area

		data = self.get_infobox_data(self.keywords["area_other"], return_first=False)
		for d in data:
			# look for convert template - {{convert|...}}
			match = re.search(r"\{\{(?:convert|cvt)\|([^\}]+)\}\}", d, re.I)
			if match:
				area = match.group(1)
				area = area.split("|")
				if len(area) >= 2:
					number, unit = (area[0].strip(), area[1].strip())
					if unit == "-":
						unit = area[3].strip()
					number = fix_area(number)
					number = self.convert_units(number, unit)
					return number if number else ""
			
			# e.g.: '20sqmi', '10 km2', ...
			area = re.sub(r"\(.+\)", "", d).strip()
			match = re.search(r"^([\d,\.]+)(.*)", area, re.I)
			if match:
				number, unit = (match.group(1), match.group(2).strip())				
				unit = unit if unit else "km2"
				number = fix_area(number)
				number = self.convert_units(number, unit)
				return number if number else ""

		# debugger.log_message(f"Error: unidentified area")
		return ""

	##
	# @brief extracts and assigns population from infobox
	def assign_population(self):
		data = self.get_infobox_data(self.keywords["population"], return_first=True)
		if data:
			pop = re.sub(r"\(.*?\)", "", data)
			pop = re.sub(r"\{\{nowrap\|([^\{]*?)\}\}", r"\1", pop)
			pop = re.sub(r"&nbsp;", "", pop)
			pop = re.sub(r"(?<=\d)\s(?=\d)", "", pop)
			pop = re.sub(r",(?=\d{3})", "", pop)
			pop = re.sub(r"\{\{circa\|([^\|]+).*?\}\}", r"\1", pop)
			pop = re.sub(r"\{\{.*?\}\}", "", pop).strip()
			match = re.search(r"uninhabited|neobydlen|bez.+?obyvatel", pop, flags=re.I)
			if match:
				pop = "0"
			match = re.search(r"^(\d+)(?:\s?([^\s]+))?", pop)
			if match:
				number = match.group(1).strip()
				coef = match.group(2)
				if coef:
					coef = coef.strip()
					coef = self.core_utils.get_coef(coef)
					number = str(int(float(number) * coef))
					pop = number
				else:
					pop = number
			else:
				pop = ""
			if re.search(r"plainlist", data, flags=re.I):
				pop = ""
			return pop
		return ""

	##
	# @brief converts units to metric system
	# @param number - number to be converted <string>
	# @param unit - unit abbreviation
	# @param round_to - to how many decimal points will be rounded to (default: 2)
	# @return converted rounded number as a string
	def convert_units(self, number, unit, round_to=2):
		try:
			number = float(number)
		except:
			debug.log_message(f"Error: couldn't conver string to float: {number}")
			return ""
		unit = unit.lower()

		SQMI_TO_KM2 = 2.589988
		SQFT_TO_KM2 = 9.2903E-8
		HA_TO_KM2 = 0.01
		ACRE_TO_KM2 = 0.00404685642
		M2_TO_KM2 = 0.000001
		MI2_TO_KM2 = 2.589988
		FT_TO_M = 3.2808
		MI_TO_KM = 1.609344
		CUFT_TO_M3 = 0.028317
		FT3_TO_M3 = 0.0283168466
		L_TO_M3 = 0.001

		accepted_untis = ["sqkm", "km2", "km²", "sq km", "square kilometres", "km", "kilometres", "kilometers", "m", "meters", "metres", "m3", "m3/s", "m³/s"]
		if unit in accepted_untis:
			return str(number if number % 1 != 0 else int(number))

		if unit == "sqmi":
			number = round(number * SQMI_TO_KM2, round_to)
		elif unit == "sqft":
			number = round(number * SQFT_TO_KM2, 5)
		elif unit in ("mi", "mile", "miles"):
			number = round(number * MI_TO_KM,round_to)
		elif unit in ("ft", "feet"):
			number = round(number / FT_TO_M, round_to)
		elif unit in ("cuft/s", "cuft"):
			number = round(number * CUFT_TO_M3,round_to)
		elif unit == "ft3/s":
			number = round(number * FT3_TO_M3, round_to)
		elif unit == "l/s":
			number = round(number * L_TO_M3, round_to)
		elif unit == "ha":
			number = round(number * HA_TO_KM2, round_to)
		elif unit in ("acres", "acre"):
			number = round(number * ACRE_TO_KM2, round_to)
		elif unit == "m2":
			number = round(number * M2_TO_KM2, round_to)
		elif unit == "mi2":
			number = round(number * MI2_TO_KM2, round_to)
		else:
			debug.log_message(f"Error: unit conversion error ({unit}, {self.link})")
			return ""

		return str(number if number % 1 != 0 else int(number))

	##
	# @brief extracts image data from the infobox
	def extract_images(self):
		if len(self.extracted_images):
			extracted_images = [img.strip().replace(" ", "_") for img in self.extracted_images]
			extracted_images = [self.get_image_path(img) for img in extracted_images]
			self.images = "|".join(extracted_images)

		data = self.get_infobox_data(self.keywords["image"], return_first=False)
		for d in data:
			image = d.replace("\n", "")
			if not image.startswith("http"):
				if re.search(r"\{\{(?:maplink|#property).*?\}\}", image, re.I):
					continue
				image = self.get_images(image)
				self.images += image if not self.images else f"|{image}"

	##
	# @brief removes wikipedia formatting and assigns image paths to the images variable
	# @param image - image data with wikipedia formatting
	def get_images(self, image):
		result = []

		image = re.sub(r"file:", "", image, flags=re.I)
		
		images = []
		
		if re.search(r"\{|\}", image):
			wikicode = parser.parse(image)
			templates = wikicode.filter_templates(wikicode)
			for t in templates:
				params = t.params
				for p in params:
					if re.search(r"image|photo|[0-9]+", str(p.name), re.I):
						if re.search(r"\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)", str(p.value), re.I):
							images.append(str(p.value))

		if not len(images):
			images.append(image)
		
		images = [re.sub(r"^(?:\[\[(?:image:)?)?(.*?(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)).*$", r"\1", img, flags=re.I) for img in images]
		images = [img.strip().replace(" ", "_") for img in images]

		result = [self.get_image_path(img) for img in images]

		return "|".join(result)

	##
	# @brief generates server path from an image name
	# @param image - image name 
	@staticmethod
	def get_image_path(image):
		image_hash = md5(image.encode("utf-8")).hexdigest()[:2]
		image_path = f"wikimedia/commons/{image_hash[0]}/{image_hash}/{image}"
		return image_path

	##
	# @brief tries to extract the first sentence from the first paragraph
	# @param paragraph - first paragraph of the page <string>
	#
	# removes the wikipedia formatting and assigns the description variable if it is empty
	# but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
	#
	# e.g.: '''Vasily Vasilyevich Smyslov''' (24 March 1921 – 27 March 2010) was a [[Soviet people|Soviet]] ...
	def get_first_sentence(self):
		paragraph = self.first_paragraph.strip()		
		if paragraph and paragraph[-1] != '.':
			paragraph += '.'		

		# TODO: make this better -> e.g.: Boleslav Bárta - ... 90. let ...
		keywords = self.keywords["sentence"]
		paragraph = re.sub(r"\[http.*?\s(.+?)\]", r"\1", paragraph)
		pattern = r"('''.*?'''.*?(?: (?:" + f"{'|'.join(keywords)}" + r") ).*?(?<!\s[A-Z][a-z])(?<![\s\.\"][A-Z])\.)"
		match = re.search(pattern, paragraph)
		if match:
			# removing templates
			sentence = match.group(1)
			sentence = re.sub(r"&nbsp;", " ", sentence)
			sentence = re.sub(r"\[\[(?:file|soubor|image):.*?\]\]", "", sentence, flags=re.I)
			sentence = re.sub(r"\[\[([^\|]*?)\]\]", r"\1", sentence)
			sentence = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", sentence)
			sentence = re.sub(r"\[|\]", "", sentence)
			# removing pronounciation and spelling
			sentence = re.sub(r"\{\{(?:IPA|respell|pronunciation).*?\}\}[,;]?", "", sentence)

			sentence = re.sub(r"\([\s,;]*\)", "", sentence)
			sentence = re.sub(r"\([\s,;]+", "(", sentence)
			sentence = re.sub(r"[\s,;]+\)", ")", sentence)
			sentence = re.sub(r"[ \t]{2,}", " ", sentence)
			self.first_sentence = sentence

	##
	# @brief serializes alias data
	# @param nametype - ???
	# @param lang - abbr
	# @return dictionary with data
	def get_alias_properties(self, nametype, lang=None):
		return {KEY_LANG: lang, KEY_NAMETYPE: nametype}

	##
	# @brief gets aliases from infobox
	def get_infobox_aliases(self):
		keys = self.keywords["infobox_name"]
		data = self.get_infobox_data(keys, False)
		for d in data:
			if re.search(r"nezveřejněn|neznám|unknown", d, re.I):
				continue
			if self.prefix.startswith("person") and self.prefix != "person:group":
				match = re.search(r"\((.*?)\)$", d)
				if match:					
					alias = re.sub(r"\(.*?\)", "", match.group(1)).strip()
					alias = alias.replace("\"", "")
					match = re.search(r"^in (\w+) (.+)", alias)
					if match:
						lang = match.group(1).lower()
						alias = match.group(2)
						if lang in self.langmap:
							lang = self.langmap[lang]
							self.aliases[alias] = self.get_alias_properties(None, lang)
						else:
							self.aliases[alias] = self.get_alias_properties(None, None)
					else:
						self.aliases[alias] = self.get_alias_properties(None, None)
					d = re.sub(r"\(.*?\)$", "", d).strip()
				
				match = re.search(r"^.+?[\"\(](.+?)[\"\)].+$", d)
				if match:
					surname = self.title.split()[-1]
					name = match.group(1)
					alias = f"{name} {surname}"
					self.aliases[alias] = self.get_alias_properties(None, None)
					d = re.sub(r"(^.+?)\s[\"\(].+?[\"\)](.+$)", r"\1\2", d)

			d, aliases = self.remove_lang_templates(d)			
			if len(aliases):
				for span in aliases:
					alias, lang = span
					self.aliases[alias] = self.get_alias_properties(None, lang)
				continue
			
			d = re.sub(r"'{2,3}", "", d)
			d = re.sub(r"&#39;", "'", d)
			d = re.sub(r"&zwj;", "'", d)
			d = re.sub(r"\{\{.*\}\}", "", d, flags=re.DOTALL)
			d = re.sub(r"\[|\]", "", d)
			d = re.sub(r"\(.*?\)", "", d).strip()
			if d:
				self.aliases[d] = self.get_alias_properties(None, None)

		keys = self.keywords["infobox_names"]
		data = self.get_infobox_data(keys, False)
		for d in data:
			if re.search(r"nezveřejněn|neznám|unknown", d, re.I):
				continue
			d = d.replace("\n", " ")
			d = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", d)
			d = re.sub(r"\[|\]", "", d)
			d = re.sub(r"\{\{small\|([^\}]*?\{\{.*?\}\}.*?)\}\}", r"\1", d)
			d = re.sub(r"\{\{small\|(.*?)\}\}", r"\1", d)
			d = re.sub(r"<br ?/?>", ", ", d)
			d = d.strip(".")

			d, array = self.remove_list_templates(d)
			if len(array):
				for a in array:
					a = re.sub(r"'{2,3}|\"", "", a)
					a = re.sub(r"\(.*?\)", "", a).strip()
					if re.search(r":$", a):
						continue
					self.aliases[a] = self.get_alias_properties(None, None)

			d = re.sub(r"[ \t]{2,}", "*", d)

			# names separeted by a character
			if re.search(r"[,*]", d):
				d = re.sub(r"\(.*?\)", "", d)
				d = re.sub(r"\"|'{2,}", "", d)
				for sep in [",", "*"]:
					d = d.split(sep)
					if len(d) > 1:
						d = [s.strip() for s in d if s]
						for v in d:
							v = re.sub(r"[\w\s]+:", "", v)
							v = v.replace("*", "").strip()
							lang = ""
							match = re.search(r"\{\{in lang\|(.*?)\}\}", v)							
							if match:
								lang = match.group(1).strip()
								v = re.sub(r"\{\{in lang\|.*?\}\}", "", v).strip()
							v, array = self.remove_lang_templates(v, False)
							if len(array):
								for span in array:
									alias, lang = span
									self.aliases[alias] = self.get_alias_properties(None, lang)
							else:
								match = re.search(r"\{\{(?:native (?:name|phrase))\|(.*?)\|(.*?)(?:\|.*?)?\}\}", v)
								if match:
									lang = match.group(1)
									v = match.group(2)
								self.aliases[v] = self.get_alias_properties(None, lang if lang else None)
						break
					else:
						d = d[0]
				return

			d, array = self.remove_lang_templates(d, False)
			for span in array:
				alias, lang = span
				self.aliases[alias] = self.get_alias_properties(None, lang)

			match = re.search(r"\{\{(?:native (?:name|phrase))\|(.*?)\|(.*?)(?:\|.*?)?\}\}", d)
			if match:
				lang = match.group(1)
				alias = match.group(2)
				self.aliases[alias] = self.get_alias_properties(None, lang)
				return				

			d = d.replace('"', "")
			if d:
				d = re.sub(r"\(.*?\)", "", d).strip()
				self.aliases[d] = self.get_alias_properties(None, None)

	##
	# @brief removes wikipedia link templates (plainlists, unbulleted lists, hlists, ...)
	# @param value - string with list template
	# @return tuple of the string without the template and array with data extracted from the template
	@staticmethod
	def remove_list_templates(value):
		array = []
		spans = []
		
		patterns = [
			r"\{\{(?:(?:indented\s)?plainlist|flatlist)\s*?\|",
			r"\{\{(?:hlist|ubl|(?:unbulleted|collapsible)\slist)\s*?\|"
		]
		
		for p in patterns:
			match = re.search(p, value, flags=re.I)
			if match:
				start = match.span()[0]
				origin, end, found, indent = (start, start, False, 0)
				for c in value[start:]:
					if c == '{':
						indent += 1
					elif c == '}':
						indent -= 1
					elif c == '|' and not found:
						origin = end + 1
						found = True
					elif c == '|' and indent == 2:
						value = value[:end] + '*' + value[end+1:]
					end += 1
					if indent == 0:
						break
				spans.append((start, origin, end))
		
		for span in sorted(spans, reverse=True):
			start, origin, end = span
			array.append(value[origin:end-2])
			value = value[:start] + value[end:]
		
		extracted = []
		for a in array:
			a = a.split("*")
			a = [i.strip() for i in a]
			a = [i for i in a if i]
			extracted += a

		return (value, extracted)
	
	##
	# @brief gets native names from infobox and removes wikipedia formatting 
	def get_native_names(self):
		keys = self.keywords["native_name_lang"]
		native_lang = self.get_infobox_data(keys)
		if native_lang:
			native_lang = native_lang.strip(":").lower()
			native_lang = re.sub(r"\[|\]", "", native_lang)
			match = re.search(r"lang-(\w+)", native_lang)
			if match:
				native_lang = match.group(1)
			native_lang = native_lang.replace(",", "-")
			native_lang = native_lang.split("-")
			native_lang = native_lang[0]
			if len(native_lang) != 2:
				if native_lang in self.langmap:
					native_lang = self.langmap[native_lang]
			if len(native_lang) > 3:
				debug.log_message(f"Error: unsoported language found in native name extraction -> {native_lang}")

		keys = self.keywords["native_name"]
		data = self.get_infobox_data(keys)
		if data:
			data = re.sub(r"&nbsp;", " ", data, flags=re.I)
			data = re.sub(r"{{okina}}|{{wbr}}", "", data, flags=re.I)
			data = re.sub(r"\{\{Nastaliq\|(.*?)\}\}", "\1", data, flags=re.I)
			data = re.sub(r"\(.*?\)", "", data)
			data = re.sub(r"\[\[(?:File|Soubor):.*?\]\]", "", data, flags=re.I)			
			
			data = self.remove_outer_templates(data).strip()
			
			# native name and transliteration templates
			a = []
			patterns = [
				r"\{\{(?:native name)\|(.*?)\|(.*?)(?:\|.*?)?\}\}",
				r"(?:'{2,3})?\{\{(?:transliteration|transl)\|(.*?)\|(?:(?:ISO|ALA-LC)\|)?(.*?)\}\}(?:'{2,3})?"
			]
			for pattern in patterns: 
				match = re.finditer(pattern, data, flags=re.I)
				for m in match:
					lang_abbr = m.group(1)
					alias = m.group(2)
					if not alias:
						continue
					alias = re.sub(r"'{2,3}", "", alias)
					self.aliases[alias] = self.get_alias_properties(None, lang_abbr)
					a.append(m.span())
				data = self.remove_spans(data, a)
				a = []

			if data:
				data, aliases = self.remove_lang_templates(data, False)
				for span in aliases:
					alias, lang = span
					self.aliases[alias] = self.get_alias_properties(None, lang)

			# ''alias''
			pattern = r"'{2,3}(.*?)'{2,3}"
			match = re.finditer(pattern, data, flags=re.I)
			for m in match:
				alias = m.group(1)
				if not re.search(r"\{\{.*?\}\}", alias):
					alias = self.remove_templates(alias)
					if alias:
						self.aliases[alias] = self.get_alias_properties(None, None if not native_lang else native_lang)
						a.append(m.span())
			data = self.remove_spans(data, a)			
			
			data = re.sub(r"\{\{.*\}\}", "", data, flags=re.DOTALL)
			data = re.sub(r"[ \t]+", " ", data)
			data = data.strip()
			if re.search(r"\w+", data):
				self.aliases[data] = self.get_alias_properties(None, None if not native_lang else native_lang)

	##
	# @brief cuts out templates from string given an array of spans with string indexes
	# @param string with templates
	# @param array of spans with string indexes
	# @return string without templates
	@staticmethod
	def remove_spans(string, spans):
		for span in sorted(spans, reverse=True):
			start, end = span
			string = string[:start] + string[end:]
		return string

	##
	# @brief removes indented templates (e.g.: {{nobold|{{lang|en|example}}}})
	# @param content - string with idented template
	# @return string without indented template
	@staticmethod
	def remove_outer_templates(content):
		patterns = [
			r"\{\{nobold\|",
			r"\{\{small(?:er)?\|",
			r"\{\{nowrap\|"
		]
		for p in patterns:
			spans = []
			match = re.finditer(p, content, flags=re.I)
			for m in match:				
				start = m.span()[0]
				origin = start
				end = start
				found = False
				indent = 0
				for c in content[start:]:
					if c == '{':
						indent += 1
					elif c == '}':
						indent -= 1
					elif c == '|' and not found:
						origin = end + 1
						found = True					
					end += 1
					if indent == 0:
						break
				spans.append((start, origin, end-2))
		
			for span in sorted(spans, reverse=True):
				start, origin, end = span
				content = content[:start] + content[origin:end] + content[end+2:]
		
		content = re.sub(r"[ \t]+", " ", content)
		
		return content
	
	##
	# @brief removes wikipedia lang templates from the first sentence
	def get_lang_aliases(self):
		sentence = self.first_sentence
		
		sentence, aliases = self.remove_lang_templates(sentence)
		for span in aliases:
			alias, lang = span
			self.aliases[alias] = self.get_alias_properties(None, lang)

		self.first_sentence = sentence

	##
	# @brief removes wikipedia lang templates from given string
	# @param data - string with lang templates
	# @param replace - bool, if true it leaves extracted data in, if false it removes the entire template
	# @return tuple with string without templates and the extracted data
	def remove_lang_templates(self, data, replace=True):
		spans = []
		aliases = []

		patterns = self.keywords["lang_alias_patterns"]
		for p in patterns:
			match = re.finditer(p, data, flags=re.I)
			for m in match:
				lang = m.group(1).strip()
				if len(lang) > 2:
					lang = lang if lang not in self.langmap else self.langmap[lang]
				if len(lang) < 2 or len(lang) > 3:
					debug.log_message(f"Error: invalid lang tag - {lang} ({self.link})")
					continue
										
				alias = m.group(2)
				alias = alias.replace("'", "").strip()
				if re.search(r"\{|\}|=", alias):
					# debug.log_message(f"{data}")
					continue
				start, end = m.span()
				aliases.append((alias, lang))
				spans.append((start, end, alias))
			
		for s in sorted(spans, reverse=True):
			start, end, alias = s
			if replace:
				data = data[:start] + alias + data[end:]
			else:
				data = data[:start] + data[end:]
		
		return (data, aliases)

	##
	# @brief extracts aliases from the first sentence for non person entities
	def extract_non_person_aliases(self):
		sentence = self.first_sentence
		match = re.findall(r"'{3}(.*?)'{3}", sentence)
		for m in match:
			m = re.sub(r"\{\{.*?\}\}", "", m)
			if m not in self.aliases:
				m = re.sub(r"'{2,}", "", m)
				# TODO: test this on more data, maybe you don't need to sub this, rather make it another alias
				# e.g.: Kuban People's Republic (KPR), Kuban National Republic (KNR)
				m = re.sub(r"\"", "", m)
				m = re.sub(r"\(.*?\)", "", m).strip()
				m = re.sub(r"[ ,]{2,}", ", ", m).strip()
				m = m.strip(",;")
				# i ě -> https://cs.wikipedia.org/wiki/Chrudim
				if len(m) > 1:				
					self.aliases[m] = self.get_alias_properties(None, self.lang)
		sentence = re.sub(r"'{3}", "", sentence)
		
		# can't extract aliases from "" 
		# quotes don't always contain aliases 
		
		match = re.search(r"(\w+):\s*([^\(\{]+?)(?:'{2,}|,|;|\))", sentence)
		# sentence = re.sub(r"'{2,3}", "", sentence)
		if match:
			lang = match.group(1).lower()
			alias = match.group(2)
			if self.title == "Brazil":
					debug.log_message(alias)
			alias = re.sub(r"\{\{.*?\}\}", "", alias).strip()
			alias = re.sub(r"\"", "", alias)
			alias = re.sub(r"'{2,3}", "", alias)
			if alias and lang in self.langmap and len(lang) > 2:
				lang = self.langmap[lang]
				self.aliases[alias] = self.get_alias_properties(None, self.lang)

		aliases = self.core_utils.specific_aliases(self)
		for span in aliases:
			alias, lang = span
			self.aliases[alias] = self.get_alias_properties(None, None)

	##
	# @brief serializes all aliases into a string separated by |
	def serialize_aliases(self):
		self.aliases.pop(self.title, None)

		preserialized = set()
		for alias, properties in self.aliases.items():
			tmp_flags = ""
			for key, value in properties.items():
				if key == KEY_LANG and value is None:
					value = LANG_UNKNOWN
				if key != KEY_NAMETYPE or value is not None:
					tmp_flags += f"#{key}={value}"
			preserialized.add(alias + tmp_flags)

		return "|".join(preserialized)
	
