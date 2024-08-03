#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file country_utils.py
# @brief cs specific country utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re

class CountryUtils:
	##
	# @brief assigns country prefix
	@staticmethod
	def assign_prefix(categories):
		# prefix - zaniklé státy
		content = "\n".join(categories)
		if re.search(r"Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie)", content, re.I):
			return "country:former"
		
		return "country"
	