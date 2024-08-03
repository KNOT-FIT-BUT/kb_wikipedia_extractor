#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file geo_utils.py
# @brief cs specific geo utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re

class GeoUtils:
	
	##
	# @brief assigns prefix based on infobox names
	@staticmethod
	def assign_prefix(geo):
		if (re.search(r"poloostrovy\s+(?:na|ve?)", "\n".join(geo.categories), re.I)
				or re.search(r"poloostrov", geo.original_title, re.I)):
			return "geo:peninsula"
		elif (geo.infobox_name in ["reliéf", "hora", "průsmyk", "pohoří", "sedlo"] 
				or re.search(r"reliéf|hora|průsmyk|pohoří|sedlo", geo.original_title, re.I)):
			return "geo:relief"
		elif (geo.infobox_name == "kontinent"
				or re.search(r"kontinent", geo.original_title, re.I)):
			return "geo:continent"
		elif (geo.infobox_name == "ostrov"
				or re.search(r"ostrov", geo.original_title, re.I)):
			return "geo:island"
		elif (geo.infobox_name == "vodopád"
				or re.search(r"vodopád", geo.original_title, re.I)):
			return "geo:waterfall"
		else:
			return "geo:unknown"
