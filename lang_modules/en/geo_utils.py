#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file geo_utils.py
# @brief en specific geo utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re

class GeoUtils:
	##
    # @brief assigns prefix based on infobox name
    #
    # geo:waterfall, geo:island, geo:relief, geo:peninsula or geo:continent
	@staticmethod
	def assign_prefix(geo):
		prefix = "geo:"
		name = ""

		pattern = r"(waterfall|islands?|mountain|peninsulas?|continent)"
		match = re.search(pattern, geo.infobox_name, re.I)
		if match:
			name = match.group(1).lower()

		if name in ("island", "islands"):
			prefix += "island"
		elif name == "mountain":
			prefix += "relief"
		elif name == "peninsulas":
			prefix += "peninsula"
		else:
			prefix += name

		if prefix == "geo:":
			categories = " ".join(geo.categories).lower()
			if "mountain ranges" in categories or "mountains" in categories:
				prefix += "relief"
			elif "waterfalls" in categories:
				prefix += "waterfall"
			elif "islands" in categories or "atols" in categories:
				prefix += "island"
			elif "peninsulas" in categories:
				prefix += "peninsula"
			else:
				prefix += "unknown"

		return prefix
