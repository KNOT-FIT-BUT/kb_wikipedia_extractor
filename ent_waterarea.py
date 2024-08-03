#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_waterarea.py
# @brief contains EntWaterArea class - entity used for lakes, seas and oceans
#
# @section ent_information entity information
# - continents
# - latitude
# - longtitude
# - area
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re
from debugger import Debugger as debug
from ent_core import EntCore

utils = {
	"en": None,
	"cs": None
}

##
# @class EntWaterArea
# @brief entity used for lakes, seas and oceans
class EntWaterArea(EntCore):
	##
    # @brief initializes the waterarea entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		super(EntWaterArea, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)
		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.continents,
			self.latitude,
			self.longitude,
			self.area
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()		
		self.continents = self.core_utils.assign_continents(self)
		self.extract_non_person_aliases()
