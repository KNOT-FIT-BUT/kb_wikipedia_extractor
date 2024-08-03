#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file stats.py
# @brief script for generating statistics after extraction
# @author created by Jan Kapsa (xkapsa00)
# @date 02.10.2022

import re
from datetime import datetime, timedelta

##
# @brief generates statistics after extraction was run
def gen_stats():
	entities = {}
	delta_sum = timedelta()
	total_pages = 0
	time_total = ""
	identification = {}
	# get entity information from head
	with open("outputs/HEAD-KB", "r") as f:
		lines = f.readlines()
		for line in lines:
			split = line.split("\t")
			match = re.search(r"<(.*?)>", split[0])
			if match:
				entity = match.group(1)
				entities[entity] = dict()
				entities[entity]["count"] = 0
				for i in range(3, len(split)):
					key = split[i]
					key = re.sub(r"\{.*?\}", "", key)
					key = key.lower()
					if key in ["original_wikiname", "wikipedia link"]:
						continue
					if key == "wiki backlinks":
						break
					entities[entity][key] = [i, 0]
	# get entity data from kb
	with open("outputs/KBstatsMetrics.all", "r") as f:
		lines = f.readlines()
		for line in lines:
			split = line.split("\t")
			entity = split[1]
			entities[entity]["count"] += 1
			for key in entities[entity].keys():
				if key == "count":
					continue
				data = split[entities[entity][key][0]]
				if data != "":
					entities[entity][key][1] += 1
	# get stats from out file
	with open("outputs/kb.out", "r") as f:
		lines = f.readlines()
		for line in lines:
			split = line.split(";")[0]
			split = split.split(",")
			if split[0] == "time_avg":
				t = datetime.strptime(split[1], "%H:%M:%S.%f")
				delta_sum += timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
				total_pages += int(split[2])
			elif split[0] == "time_total":
				t = datetime.strptime(split[1], "%H:%M:%S.%f")
				delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
				time_total = pretty_time_delta(delta.total_seconds())
			elif split[0] == "id_stats":
				key = split[1]
				number = int(split[2])
				if key not in identification:
					# count. sum, min, max
					identification[key] = [0, 0, None, None]
				identification[key][0] += 1
				identification[key][1] += number
				if identification[key][2] is None or identification[key][2] > number:
					identification[key][2] = number
				if identification[key][3] is None or identification[key][3] < number:
					identification[key][3] = number
			else:
				continue
	with open("outputs/stats.log", "w") as f:

		# time and general stats
		f.write("== general statistics ==\n")
		f.write("\n")
		f.write("{:<20}{:<15}\n".format("total pages", total_pages))
		f.write("{:<20}{:<15}\n".format("total time", time_total))
		f.write("{:<20}{:<15}\n".format("avg. time for page", str(delta_sum/total_pages)))

		f.write("\n")

		# count
		f.write("== entities ==\n")
		f.write("- total and individual counts of entities\n")
		f.write("\n")
		arr = []
		total = 0
		for key, item in entities.items():
			arr.append((key, item["count"]))
			total += item["count"]
		f.write("{:<20}{}\n".format("total", total))
		f.write("--------------------------------\n")
		for item in sorted(arr, key=lambda x: x[1], reverse=True):
			f.write("{:<20}{}\n".format(item[0], item[1]))

		f.write("\n")

		# identification
		f.write("== identification ==\n")
		f.write("- shows how much identification points each entity got during the identification\n")
		f.write("\n")
		f.write("{:<20}{:<15}{:<15}{:<15}\n".format("entity","avg","min","max"))
		f.write("----------------------------------------------------------\n")
		for key, item in sorted(identification.items(), key=lambda x: round(x[1][1]/x[1][0],2), reverse=True):
			f.write("{:<20}{:<15}{:<15}{:<15}\n".format(key,round(item[1]/item[0],2),item[2],item[3]))

		f.write("\n")

		# emptiness
		f.write("== entity emptiness ==\n")
		f.write("- shows how much of invidual information was extracted during the extraction\n")
		f.write("- (person: aliases 50% means 50% of person entities had aliases extracted)\n")
		f.write("\n")
		for key, item in entities.items():
			if item["count"] != 0:
				count = item["count"]
				f.write(f"{key} ({item['count']})\n")
				f.write("--------------------------------\n")
				for k, i in item.items():
					if k == "count":
						continue
					f.write("{:<20}{}%\n".format(k, round(i[1]/count*100,2)))
				f.write("\n")

##
# @brief prints time in a readable format
# source: https://gist.github.com/thatalextaylor/7408395
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

if __name__ == "__main__":
	gen_stats()