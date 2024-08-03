#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file country_utils.py
# @brief en specific country utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re

class CountryUtils:
	
	##
	# @brief assigns prefix based on categories
	@staticmethod
	def assign_prefix(categories):
		for category in categories:
			# TODO: "developed" is too specific
			if "developed" in category:
				continue
			if re.search(r"former.*?countries", category.lower(), re.I):
				return "country:former"
		return "country"
