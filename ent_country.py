#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_country.py
# @brief contains EntCountry class - entity used for countries
#
# @section ent_information entity information
# - area
# - population
# - latitude
# - longtitude
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from ent_core import EntCore

from debugger import Debugger as debug

from lang_modules.en.country_utils import CountryUtils as EnUtils
from lang_modules.cs.country_utils import CountryUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntCountry
# @brief entity used for countries
class EntCountry(EntCore):
	##
    # @brief initializes the country entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		super(EntCountry, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.latitude,
			self.longitude,
			self.area,
			self.population
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions) and assigns prefix
	def assign_values(self, lang):
		lang_utils = utils[lang]
		self.prefix = lang_utils.assign_prefix(self.categories)
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()
		self.population = self.assign_population()

		self.extract_non_person_aliases()
