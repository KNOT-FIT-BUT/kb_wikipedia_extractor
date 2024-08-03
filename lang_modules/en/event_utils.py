#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file event_utils.py
# @brief en specific event utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re
from lang_modules.en.core_utils import CoreUtils

class EventUtils:

	##
    # @brief extracts and assigns start date and end date variables from infobox
	@staticmethod
	def assign_dates(infobox_data):
		start_date = ""
		end_date = ""

		keys = ["year", "start_date", "first_aired", "election_date"]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = CoreUtils.extract_date(data)
				start_date = data[0]

		keys = ["end_date"]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = CoreUtils.extract_date(data)
				end_date = data[0]

		keys = ["date"]
		
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				split = data.split("–")
				split = [item.strip() for item in split if item != ""]
				if len(split) == 1:
					date = CoreUtils.extract_date(split[0])
					start_date = date[0]
					end_date = date[1]						
					break
				else:
					
					# 19-25 September 2017 -> 19 September 2017 - 25 September 2017
					if re.search(r"^[0-9]+$", split[0]):
						match = re.search(r"^[0-9]+?\s+?([a-z]+?\s+?[0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return (start_date, end_date)

					# January-September 2017 -> January 2017 - September 2017
					if re.search(r"^[a-z]+$", split[0], re.I):
						match = re.search(r"^[a-z]+?\s+?([0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return (start_date, end_date)

					start_date = CoreUtils.extract_date(split[0])[0]
					end_date = CoreUtils.extract_date(split[1])[0]

		return (start_date, end_date)
