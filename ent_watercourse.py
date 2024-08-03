#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_watercourse.py
# @brief contains EntWaterCourse class - entity used for rivers, creeks, streams, etc.
#
# @section ent_information entity information
# - continents
# - latitude
# - longtitude
# - length
# - area
# - streamflow
# - source_loc
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re
from debugger import Debugger as debug
from ent_core import EntCore

##
# @class EntWaterCourse
# @brief entity used for rivers, creeks, streams, etc.
class EntWaterCourse(EntCore):
	##
    # @brief initializes the watercourse entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		super(EntWaterCourse, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.length = ""
		self.area = ""
		self.streamflow = ""
		self.source_loc = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.continents,
			self.latitude,
			self.longitude,
			self.length,
			self.area,
			self.streamflow,
			self.source_loc
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):		
		self.lang = lang
		self.continents = self.core_utils.assign_continents(self)
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()
		self.assign_length()
		self.assign_streamflow()
		self.assign_source()
		self.extract_non_person_aliases()

	##
    # @brief extracts and assigns source location from infobox
	def assign_source(self):
		def fix_source(source):
			source = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", source)
			source = re.sub(r"\[|\]", "", source)
			source = re.sub(r"'{2}", "", source)
			source = re.sub(r"{{.*?}}", "", source).replace("()", "")
			source = source.strip().strip(",").strip()
			return source

		data = self.get_infobox_data(self.keywords["source"])
		if data:
			data = fix_source(data)
			self.source_loc = data

	##
    # @brief extracts and assigns streamflow from infobox
	def assign_streamflow(self):
		def fix_streamflow(flow):
			flow = re.sub(r"\(.*?\)", "", flow).strip()
			flow = re.sub(r"&nbsp;", "", flow)
			flow = re.sub(r",(?=\d{3})", "", flow)
			match = re.search(r"\{\{(?:convert|cvt)\|([\d,\.]+)\|([^\|]+)(?:\|.*?)?\}\}", flow, flags=re.I)
			if match:
				number = match.group(1).strip()
				unit = match.group(2).strip()
				flow = self.convert_units(number, unit)
			flow = re.sub(r"(?<=\d)\s(?=\d)", "", flow)
			flow = re.sub(r"^\D*(?=\d)", "", flow)
			flow = flow.replace(",", ".")
			match = re.search(r"^([\d\.,]+)(?:\s([^\s]+))?", flow)
			if match:
				number = match.group(1)
				unit = match.group(2)
				if unit:
					flow = self.convert_units(number, unit)
				else:
					flow = number
			else:
				flow = ""
			return flow

		data = self.get_infobox_data(self.keywords["streamflow"])
		if data:
			data = fix_streamflow(data)
			self.streamflow = data

	##
    # @brief extracts and assigns length from infobox
	def assign_length(self):
		def fix_length(length):
			length = re.sub(r"\(.*?\)", "", length)
			length = re.sub(r"&nbsp;", " ", length)
			length = re.sub(r"(?<=\d)\s(?=\d)", "", length)
			length = re.sub(r",(?=\d{3})", "", length)
			length = length.replace(",", ".")
			match = re.search(r"\{\{(?:convert|cvt)\|([\d,\.]+)\|([^\|]+)(?:\|.*?)?\}\}", length, flags=re.I)
			if match:
				number = match.group(1).strip()
				unit = match.group(2).strip()
				length = self.convert_units(number, unit)
			length = re.sub(r"\{\{.*?\}\}", "", length)
			match = re.search(r"^([\d\.]+)(?:\s?([^\s]+))?", length)
			if match:
				number = match.group(1).strip()
				unit = match.group(2)
				if unit:
					unit = unit.strip(".").strip()
					length = self.convert_units(number, unit)
				else:
					length = number
			else:
				length = ""
			return length

		data = self.get_infobox_data(self.keywords["length"])
		if data:
			data = fix_length(data)
			self.length = data
