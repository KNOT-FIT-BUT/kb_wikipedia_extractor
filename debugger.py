#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file debugger.py
# @brief contains TUI and functions for debugging and logging
#
# @section ideas ideas
# pause extraction every time interesting entity is found / inform about it
# print messages with color depending on their importance / meaning 
#
# @author created by Jan Kapsa (xkapsa00)
# @date 25.07.2022 

import datetime
from collections import Counter
import sys
import os

SCORE = 10

##
# @class Debugger
# @brief used for TUI, debugging and logging
class Debugger:
	##
	# @brief initializes debugger entity	
	def __init__(self):
		# TODO: add debug mode on/off switch
		
		self.debug_limit = 50000

		# time
		self.start_time = datetime.datetime.now()

		# categories
		self.infobox_names = set()
		self.category_counter = Counter()

		# identification
		self.id_count = 0
		self.id_sum = 0

	##
	# @brief clears currently updating message and prints a message with a new line 
	@staticmethod
	def print(message, print_time=True):
		if print_time:
			message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}"
		print(f"{message}\033[K")

	## 
	# @brief updates (clears) current line and writes new message 
	@staticmethod
	def update(msg):
		print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\033[K", end="\r")

	## 
	# @brief logs data into a file (prints data to stderr, which is redirected to a file)
	@staticmethod
	def log_message(message, print_time=False):		
		if print_time:
			message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}"
		print(f"{message}", file=sys.stderr)

	##
	# @brief logs entity information
	# def log_entity(self, entity, prefix):
	# 	data = []

	# 	entity_data = entity.split("\t")
	# 	data.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging entity")
	# 	empty = []
	# 	for i in range(len(entity_data)):
	# 		if entity_data[i] != "":
	# 			data.append(f"  {self.entities[prefix][i]}: {entity_data[i]}")
	# 		else:
	# 			empty.append(self.entities[prefix][i])
	# 	data.append(f"  empty: {', '.join(empty)}")
	# 	self.log_message("\n".join(data))
	
	##
	# @brief checks if entity is mostly empty (implies badly identified entity)
	def check_empty(self, entity, prefix):
		entity_data = entity.split("\t")
		score = 0
		for d in entity_data:
			if d == "":
				score += 1
		if score > SCORE:
			self.log_entity(entity, prefix)

	##
	# @brief logs the result of entity extraction (infobox, categories, first paragraph, ...)
	def log_extraction(self, title, extraction, flags=(False, False, False)):
		
		data = []

		data.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging entity extraction")
		data.append(f"title: {title}")

		# flags[0] == infobox extraction
		if flags[0]:
			if extraction["found"]:
				data.append("infobox:")
				empty = []
				for key, value in extraction["data"].items():
					if value != "":
						value = value.replace("\n", "")
						data.append(f"  {key}: {value}")
					else:
						empty.append(key)
				data.append(f"  empty: {', '.join(empty)}")
			else:
				data.append("infobox not found")
		
		# flags[1] == category extraction
		if flags[1]:
			data.append("categories:")
			for c in extraction["categories"]:
				data.append(f"  {c}")
		
		# flags[2] == paragraph extraction
		if flags[2]:
			data.append("paragraph:")
			data.append(f"  {extraction['paragraph']}")
		
		self.log_message("\n".join(data))

	##
	# @brief logs identification of an entity (how much score each entity type got)
	@classmethod
	def log_identification(cls, identification, title=None):
		# identification is a Counter
		if title:
			cls.log_message(f"identification of {title}:")
		for key, value in identification:
			if value != 0:
				cls.log_message("{:<20}{:<15}".format(key, value))

	##
	# @brief fiters data sent to stderr (stderr is redirected to out/kb.out) and logs important data into a log file (log/kb.log) 
	def log(self):
		end_time = datetime.datetime.now()
		tdelta = end_time - self.start_time
		self.print(f"completed extraction in {self.pretty_time_delta(tdelta.total_seconds())}", print_time=False)
		self.log_message(f"time_total,{tdelta};")

		log = []

		with open(os.path.join(os.path.dirname(sys.argv[0]), "outputs/kb.out"), "r") as f:
			lines = f.readlines()
			for line in lines:
				msg = line.split(";")[0]
				msg = msg.split(",")
				if msg[0] not in ["id_stats", "time_avg", "time_total"]:
					log.append(line)

		with open(os.path.join(os.path.dirname(sys.argv[0]), "outputs/kb.log"), "w") as f:
			f.writelines(log)

	##
	# @brief TUI function, prints time delta in readable format
	# source: https://gist.github.com/thatalextaylor/7408395
	@staticmethod
	def pretty_time_delta(seconds):
		seconds = int(seconds)
		days, seconds = divmod(seconds, 86400)
		hours, seconds = divmod(seconds, 3600)
		minutes, seconds = divmod(seconds, 60)
		if days > 0:
			return '%dd%dh%dm%ds' % (days, hours, minutes, seconds)
		elif hours > 0:
			return '%dh%dm%ds' % (hours, minutes, seconds)
		elif minutes > 0:
			return '%dm%ds' % (minutes, seconds)
		else:
			return '%ds' % (seconds,)
