#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file ent_organisation.py
# @brief contains EntOrganisation class - entity used for organisations
#
# @section ent_information entity information
# - founded
# - cancelled
# - location
# - type
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from ent_core import EntCore

from lang_modules.en.organisation_utils import OrganisationUtils as EnUtils

utils = {
	"en": EnUtils
}

##
# @class EntOrganisation
# @brief entity used for organisations
class EntOrganisation(EntCore):
	##
    # @brief initializes the organisation entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		super(EntOrganisation, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)

		self.founded = ""
		self.cancelled = ""
		self.location = ""
		self.type = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.founded,
			self.cancelled,
			self.location,
			self.type
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):
		lang_utils = utils[lang]
		self.founded, self.cancelled = lang_utils.assign_dates(self.infobox_data)
		self.assign_location()
		self.assign_type()

		if not self.type:
			if self.infobox_name and self.infobox_name.lower() != "organization":
				self.type = self.infobox_name

		self.extract_non_person_aliases()
	
	##
	# @brief extracts and assigns location from infobox
	def assign_location(self):
		location = ""
		country = ""
		city = ""

		keys = ["location", "headquarters", "hq_location", "area"]
		data = self.get_infobox_data(keys, return_first=True)
		if data:
			data = self.remove_templates(data)
			location = data
		
		keys = ["location_country", "country", "hq_location_country"]
		data = self.get_infobox_data(keys, return_first=True)
		if data:
			data = self.remove_templates(data)
			country = data

		keys = ["location_city", "hq_location_city"]
		data = self.get_infobox_data(keys, return_first=True)
		if data:
			data = self.remove_templates(data)
			city = data

		if city != "" and country != "":
			self.location = f"{city}, {country}"
		else:
			if location != "":
				self.location = location
			elif country != "":
				self.location = country
			else:
				self.location = city

	##
    # @brief extracts and assigns type from infobox
	def assign_type(self):
		data = self.get_infobox_data(self.keywords["type"], return_first=True)
		if data:
			data = self.remove_templates(data)
			self.type = data
