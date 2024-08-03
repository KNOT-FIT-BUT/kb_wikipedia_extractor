#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @mainpage Entity KB project index page
# see https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_english5 for more information...

##
# @file wiki_extract.py
# @brief main script that contains WikiExtract class that extracts and identifies entities
#
# @section how_it_works how it works
# - parses arguments
# - creates head and version
# - parses wikipedia xml dump
# - logs errors and statistics to a file
# @section parsing_xml_dump parsing the xml dump
# - loads the redirect, first sentence, identification patterns and langmap files
# - goes through the xml file and identifies entities
# - for each entity:
#   - extracts important data
#   - identifies the entity
#   - assigns a class to the entity
# - outputs extracted entities into a file
#
# @author created by Jan Kapsa (xkapsa00)
# @date 26.07.2022

import os, re, argparse, time, json, sys
from debugger import Debugger as debug
import xml.etree.cElementTree as CElTree
from datetime import datetime
from multiprocessing import Pool
from itertools import repeat
from collections import Counter
import mwparserfromhell as parser
from ent_person import EntPerson
from ent_country import EntCountry
from ent_settlement import EntSettlement
from ent_waterarea import EntWaterArea
from ent_watercourse import EntWaterCourse
from ent_geo import EntGeo
from ent_organisation import EntOrganisation
from ent_event import EntEvent
from lang_modules.en.core_utils import CoreUtils as EnCoreUtils
from lang_modules.cs.core_utils import CoreUtils as CsCoreUtils

LANG_MAP = {"cz": "cs"}

utils = {
	"en": EnCoreUtils,
	"cs": CsCoreUtils
}

PAGES_DUMP_FPATH = '{}wiki-{}-pages-articles.xml'

##
# @class WikiExtract
# @brief main class of the project, one istance is created to execute the main functions
class WikiExtract(object):
	##
	# @brief initializes the console_args variable and debugger class
	def __init__(self):
		self.console_args = None
		self.dump = None
		self.tracker = debug()

	##
	# @brief parses the console arguments
	def parse_args(self):
		parser = argparse.ArgumentParser()
		parser.add_argument(
			"-I",
			"--indir",
			default="/mnt/minerva1/nlp/corpora_datasets/monolingual/english/wikipedia/",
			type=str,
			help="Directory, where input files are located (applied for files withoud directory location only).",
		)
		parser.add_argument(
			"-l",
			"--lang",
			default="en",
			type=str,
			help="Language of processing also used for input files, when defined by version (by default) and not by files (default: %(default)s).",
		)
		parser.add_argument(
			"-d",
			"--dump",
			default="latest",
			type=str,
			help='Dump version to process (in format "yyyymmdd"; default: %(default)s).',
		)
		parser.add_argument(
			"-m",
			default=2,
			type=int,
			help="Number of processors of multiprocessing.Pool() for entity processing.",
		)
		parser.add_argument(
			"-g",
			"--geotags",
			action="store",
			type=str,
			help="Source file of wiki geo tags (with GPS locations) dump.",
		)
		parser.add_argument(
			"-p",
			"--pages",
			action="store",
			type=str,
			help="Source file of wiki pages dump.",
		)
		parser.add_argument(
			"-r",
			"--redirects",
			action="store",
			type=str,
			help="Source file of wiki redirects dump.",
		)
		parser.add_argument(
			"-s",
			"--first_sentences",
			action="store",
			type=str,
			help="Source file of wiki dump of first sentences.",
		)
		parser.add_argument(
			"--dev",
			action="store_true",
			help="Development version of KB",
		)
		parser.add_argument(
			"--test",
			action="store_true",
			help="Test version of KB",
		)
		parser.add_argument(
			"--debug",
			action="store",
			nargs="?",
			type=int,
			const=self.tracker.debug_limit,
			default=None,
			help="Number of pages to process in debug mode (default %(const)s).",
		)
		self.console_args = parser.parse_args()

		if self.console_args.m < 1:
			self.console_args.m = 1

		self.console_args.lang = self.console_args.lang.lower()
		if self.console_args.lang in LANG_MAP:
			self.console_args.lang = LANG_MAP[self.console_args.lang]

		self.tracker.debug_limit = self.console_args.debug

		self.pages_dump_fpath = self.get_dump_fpath(self.console_args.pages, PAGES_DUMP_FPATH)
		self.geotags_dump_fpath = self.get_dump_fpath(self.console_args.geotags, "{}wiki-{}-geo_tags.sql")
		self.redirects_dump_fpath = self.get_dump_fpath(self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.tsv")
		self.fs_dump_path = self.get_dump_fpath(self.console_args.first_sentences, "1st_sentences_from_{}wiki-{}-pages-articles.tsv")
		self.console_args._kb_stability = ""

		if self.console_args.dev:
			self.console_args._kb_stability = "dev"
		elif self.console_args.test:
			self.console_args._kb_stability = "test"

	##
	# @brief creates a path to the dump file
	# @param dump_file
	# @param dump_file_mask
	# @return string file path
	def get_dump_fpath(self, dump_file, dump_file_mask):
		if dump_file is None:
			dump = self.dump if self.dump is not None else self.console_args.dump
			dump_file = dump_file_mask.format(
				self.console_args.lang, dump
			)
			if self.dump is None and dump_file_mask == PAGES_DUMP_FPATH:
				# Get real file path from possible file link - main file is pages dump
				# (due to missing latest link on some files + prevention of bad links of other files)
				split_by = '-'
				real_dump_file_parts = os.readlink(
					self._get_absolute_path(dump_file)
				).split(split_by)
				dump_file_parts = dump_file.rsplit('/')[-1].split(split_by)
				for x, y in zip(dump_file_parts, real_dump_file_parts):
					if x == self.console_args.dump:
						self.dump = y
						break
		return self._get_absolute_path(dump_file)

	def _get_absolute_path(self, dump_file: str) -> str:
		if dump_file == "" or dump_file[0] == "/":
			return dump_file
		elif dump_file[0] == "." and (dump_file[1] == "/" or dump_file[1:3] == "./"):
			return os.path.join(os.getcwd(), dump_file)

		return os.path.join(self.console_args.indir, dump_file)

	##
	# @brief creates a wikipedia link given the page name
	# @param page - string containing page title
	# @return wikipedia link
	def get_link(self, page):
		wiki_link = page.replace(" ", "_")
		return f"https://{self.console_args.lang}.wikipedia.org/wiki/{wiki_link}"

	##
	# @brief creates the HEAD-KB file
	# HEAD-KB file contains individual fields of each entity
	@staticmethod
	def create_head_kb():
		entities = [
			"<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:artist>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\t{m}ART_FORMS\t{m}INFLUENCERS\t{m}INFLUENCEES\tULAN_ID\t{m}OTHER_URLS\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:fictional>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:group>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<country>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<country:former>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<settlement>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tCOUNTRY\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<watercourse>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tLENGTH\tAREA\tSTREAMFLOW\tSOURCE_LOC\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<waterarea>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:relief>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:waterfall>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tTOTAL HEIGHT\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:island>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:peninsula>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:continent>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<organisation>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tFOUNDED\tCANCELLED\tORGANISATION_TYPE\tLOCATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<event>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tSTART\tEND\tLOCATION\tEVENT_TYPE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
		]

		with open("HEAD-KB", "w", encoding="utf-8") as file:
			for entity in entities:
				file.write(entity)

	##
	# @brief creates the VERSION file
	def assign_version(self):
		str_kb_stability = f"-{self.console_args._kb_stability}" if self.console_args._kb_stability else ""

		try:
			target = os.readlink(self.pages_dump_fpath)
			matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
			if matches:
				dump_version = matches[1]
		except OSError:
			try:
				target = os.readlink(self.redirects_dump_fpath)
				matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
				if matches:
					dump_version = matches[1]
			except OSError:
				dump_version = self.console_args.dump

		with open("VERSION", "w") as f:
			f.write("{}_{}-{}{}".format(
				self.console_args.lang,
				dump_version,
				int(round(time.time())),
				str_kb_stability,
			))

	##
	# @brief loads redirects
	# @param redirects_fpath path to the file with extracted redirects
	# @return dictionary with redirects
	def load_redirects(self, redirects_fpath):
		redirects = dict()
		try:
			with open(redirects_fpath, "r") as f:
				start_time = datetime.now()
				i = 0
				debug.update(f"loading redirects: {i}")
				for line in f:
					i += 1
					debug.update(f'loading redirects: {i}')
					redirect_from, redirect_to = line.strip().split("\t")
					if redirect_to not in redirects:
						redirects[redirect_to] = [redirect_from]
					else:
						redirects[redirect_to].append(redirect_from)
				end_time = datetime.now()
				tdelta = end_time - start_time
				debug.print(f"loaded aliases ({i} in {debug.pretty_time_delta(tdelta.total_seconds())})")
		except OSError:
			debug.print(f"redirect file ({redirects_fpath}) was not found - skipping...")

		return redirects

	##
	# @brief loads langmap
	# @param langmap_fpath path to the file with langmap
	# @return dictionary with langmap
	def load_langmap(self, langmap_fpath):
		langmap = dict()

		try:
			with open(langmap_fpath, "r") as file:
				debug.update("loading langmap")
				langmap = json.load(file)
				debug.print("loaded langmap")
		except OSError:
			debug.print(f"langmap file 'langmap.json' was not found")
			debug.print(f"please generate langmap.json (use generate_langmap.json)")
			# exit(1)

		return langmap

	##
	# @brief loads first sentences
	# @param senteces_fpath path to the file with extracted first sentences
	# @return dictionary with first sentences
	def load_first_sentences(self, sentences_fpath):
		first_sentences = dict()

		try:
			with open(sentences_fpath, "r") as f:
				start_time = datetime.now()
				debug.update("loading first sentences")
				i = 0
				for line in f:
					i += 1
					debug.update(i)
					split = line.strip().split("\t")
					link = split[0]
					sentence = split[1] if len(split) > 1 else ""
					first_sentences[link] = sentence
				end_time = datetime.now()
				tdelta = end_time - start_time
				debug.print(f"loaded first sentences ({i} in {debug.pretty_time_delta(tdelta.total_seconds())})")
		except OSError:
			debug.print(f"first sentence file ({sentences_fpath}) was not found - skipping...")

		return first_sentences

	##
	# @brief loads patterns for entity recognition
	# @param patterns_fpath path to the file with patterns
	# @return dictionary with patterns
	def load_patterns(self, patterns_fpath):
		d = dict()

		try:
			with open(patterns_fpath, "r") as file:
				d = json.load(file)
			debug.print("loaded identification patterns")
		except OSError:
			debug.print("entity identification patterns were not found - exiting...")
			exit(1)

		keywords = d["keywords"]
		identification = d["identification"]
		return identification, keywords

	##
	# @brief generates default path to a file
	@staticmethod
	def get_path(fpath):
		return os.path.join(os.path.dirname(sys.argv[0]), fpath)

	##
	# @brief loads redirects, first sentences, langmap and patterns, then parses xml dump
	def parse_xml_dump(self):
		redirects =self.load_redirects(self.redirects_dump_fpath)
		langmap = self.load_langmap(self.get_path(f"json/langmap_{self.console_args.lang}.json"))
		first_sentences = self.load_first_sentences(self.fs_dump_path)
		patterns, keywords = self.load_patterns(self.get_path(f"json/patterns_{self.console_args.lang}.json"))

		# xml parser
		context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))

		ent_data = []

		curr_page_cnt = 0
		all_page_cnt = 0
		ent_count = 0

		# LOOP_CYCLE = skript bude číst a extrahovat data po blocích o velikosti [LOOP_CYCLE]
		LOOP_CYCLE = 4000
		debug_limit_hit = False

		with open("kb", "a+", encoding="utf-8") as file:
			file.truncate(0)
			event, root = next(context)
			for event, elem in context:

				if debug_limit_hit:
					break

				# hledá <page> element
				if event == "end" and "page" in elem.tag:
					# xml -> <page> -> <title>
					# xml -> <page> -> <revision>
					is_entity = False
					title = ""

					for child in elem:
						# získá title stránky
						if "title" in child.tag:
							is_entity = utils[self.console_args.lang].is_entity(child.text.lower())
							if is_entity:
								title = child.text
						# získá text stránky
						elif "revision" in child.tag:
							for grandchild in child:
								if "text" in grandchild.tag and is_entity and grandchild.text:
									if re.search(keywords["disambig_pattern"], grandchild.text, re.I):
										debug.update("found disambiguation")
										break

									# nalezení nové entity
									link = self.get_link(title)
									ent_data.append((
										title,
										grandchild.text,
										redirects[link] if link in redirects else [],
										first_sentences[link] if link in first_sentences else ""
									))

									curr_page_cnt += 1
									all_page_cnt += 1

									debug.update(f"found new page ({all_page_cnt})")

									if self.tracker.debug_limit is not None and all_page_cnt >= self.tracker.debug_limit:
										debug.print(f"debug limit hit (number of pages: {all_page_cnt})")
										debug_limit_hit = True
										break

									if curr_page_cnt == LOOP_CYCLE:
										ent_count += self.output(file, ent_data, langmap, patterns, keywords)
										ent_data.clear()
										curr_page_cnt = 0
						elif "redirect" in child.tag:
							debug.update(f"found redirect ({all_page_cnt})")
							break

					root.clear()

			if len(ent_data):
				ent_count += self.output(file, ent_data, langmap, patterns, keywords)

		debug.print("----------------------------", print_time=False)
		debug.print(f"parsed xml dump (number of pages: {all_page_cnt})", print_time=False)
		debug.print(f"processed {ent_count} entities", print_time=False)

	##
	# @brief extracts the entities with multiprocessing and outputs the data to a file
	# @param file - output file ("kb" file)
	# @param ent_data - ordered array of tuples with entity data
	# @param langmap - dictionary of language abbreviations
	# @param patterns - dictionary containing identification patterns
	# @return number of pages that were identified as entities (count of extracted entities)
	def output(self, file, ent_data, langmap, patterns, keywords):
		if len(ent_data):
			start_time = datetime.now()

			pool = Pool(processes=self.console_args.m)
			serialized_entities = pool.starmap(
				self.process_entity,
				zip(ent_data, repeat(langmap), repeat(patterns), repeat(keywords))
			)
			l = list(filter(None, serialized_entities))
			file.write("\n".join(l) + "\n")
			pool.close()
			pool.join()
			count = len(l)

			end_time = datetime.now()
			tdelta = end_time - start_time
			debug.print(f"processed {count} entities (in {debug.pretty_time_delta(tdelta.total_seconds())})")
			debug.log_message(f"time_avg,{tdelta},{len(ent_data)};")
			return count

	##
	# @brief extracts entity data, identifies the type of the entity and assigns a class
	# @param ent_data - dictionary with entity data (title, page content, ...)
	# @param langmap - dictionary of language abbreviations
	# @param patterns - dictionary containing identification patterns
	# @return tab separated string with entity data or None if entity is unidentified
	def process_entity(self, ent_data, langmap, patterns, keywords):
		title, content, redirects, sentence = ent_data

		debug.update(f"INFO: processing {title}")

		extraction = self.extract_entity_data(content, keywords)
		identification = self.identify_entity(title, extraction, patterns).most_common()

		count = 0
		for _, value in identification:
			count += value

		if count > 0:
			debug.log_message(f"id_stats,{identification[0][0]},{count};")

		# if count != 0:
		# 	debug.log_identification(identification, title=title)

		entities = {
			"person":       EntPerson,
			"country":      EntCountry,
			"settlement":   EntSettlement,
			"waterarea":    EntWaterArea,
			"watercourse":  EntWaterCourse,
			"geo":          EntGeo,
			"organisation": EntOrganisation,
			"event":        EntEvent
		}

		if identification[0][1] > 0:
			key = identification[0][0]
			if key in entities:
				entity = entities[key](title, key, self.get_link(title), extraction, langmap, redirects, sentence, keywords)
				entity.assign_values(self.console_args.lang)
				return repr(entity)

		# debug.log_message(f"Error: unidentified page: {title}")
		return None

	##
	# @brief tries to extract infobox, first paragraph, categories and coordinates
	# @param content - string containing page content
	# @return dictionary of extracted entity data
	#
	# uses the mwparserfromhell library
	def extract_entity_data(self, content, keywords):

		content = self.remove_not_important(content)

		result = {
			"found": False,
			"name": "",
			"data": dict(),
			"paragraph": "",
			"categories": [],
			"coords": "",
			"images": []
		}

		wikicode = parser.parse(content)
		templates = wikicode.filter_templates()

		infobox = None

		# look for infobox
		for t in templates:
			name = t.name.lower().strip()
			if name.startswith("infobox") and infobox is None:
				infobox = t
				name = name.split()
				name.pop(0)
				name = " ".join(name)
				result["found"] = True
				# fix names e.g.: "- spisovatel"
				name = name.strip()
				if name and name[0] == '-':
					name = name[1:].strip()
				result["name"] = self.remove_breaks(name)
			elif "coord" in name or "coords" in name:
				result["coords"] = self.remove_breaks(str(t))

		# extract infobox
		if result["found"]:
			for p in infobox.params:
				field = p.strip()
				field = [item.strip() for item in field.split("=")]
				key = field.pop(0).lower()
				value = "=".join(field)
				result["data"][key] = self.replace_breaks_by_commas(value)

		# extract first paragraph
		sections = wikicode.get_sections()
		if len(sections):
			section = sections[0]
			templates = section.filter_templates()

			for t in templates:
				if t.name.lower().startswith("infobox"):
					section.remove(t)
					break

			split = [s for s in section.strip().split("\n") if s != ""]
			while len(split):
				s = split.pop(0)
				match = re.search(r"^'''|The '''", s, flags=re.I)
				if match:
					s = s[match.span()[0]:]
					s += f" {' '.join(split)}"
					result["paragraph"] = self.remove_breaks(s.strip())
					break
		else:
			debug.log_message("Error: no first section found")

		# extract categories
		lines = content.splitlines()
		for line in lines:
			# categories
			pattern = keywords["category_pattern"]
			match = re.search(pattern, line, re.I)
			if match:
				result["categories"].append(
					self.remove_breaks(
						match.group(1).strip()
					)
				)
				continue

			# images
			match = re.search(r"\[\[(?:file|soubor):([^\]]*?)\|[^\]]*?\]\]", line, re.I)
			if match:
				value = match.group(1).strip()
				if re.search(r"\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)$", value, re.I):
					result["images"].append(self.remove_breaks(value))

		return result

	##
	# @brief uses patterns to score the entity, prefix with the highest score is later chosen as the entity identification
	# @param title - string containing page title
	# @param extracted - dictionary with extracted entity data (infobox, categories, ...)
	# @param patterns - dictionary containing identification patterns
	# @return Counter instance with identification scores
	#
	# entity is given a point for each matched pattern
	# it looks at categories, infobox names, titles and infobox fields
	# these patterns are located in a en/json/identification.json file
	#
	# @todo better algorithm for faster performance
	# @todo score weight system
	@staticmethod
	def identify_entity(title, extracted, patterns):
		counter = Counter({key: 0 for key in patterns.keys()})

		# categories
		for c in extracted["categories"]:
			for entity in patterns.keys():
				for p in patterns[entity]["categories"]:
					if re.search(p, c, re.I):
						counter[entity] += 1 if counter[entity] >= 0 else 0
				if "!categories" in patterns[entity]:
					for p in patterns[entity]["!categories"]:
						if re.search(p, c, re.I):
							if counter[entity] > 0:
								counter[entity] *= -1
							elif counter[entity] == 0:
								counter[entity] -= 1
							break

		# infobox names
		for entity in patterns.keys():
			for p in patterns[entity]["names"]:
				if re.search(p, extracted["name"], re.I):
					counter[entity] += 1 if counter[entity] >= 0 else 0
			if "!names" in patterns[entity]:
				for p in patterns[entity]["!names"]:
					if re.search(p, extracted["name"], re.I):
						if counter[entity] > 0:
							counter[entity] *= -1
						elif counter[entity] == 0:
							counter[entity] -= 1
						break

		# titles
		for entity in patterns.keys():
			for p in patterns[entity]["titles"]:
				if re.search(p, title, re.I):
					counter[entity] += 1 if counter[entity] >= 0 else 0
			if "!titles" in patterns[entity]:
				for p in patterns[entity]["!titles"]:
					if re.search(p, title, re.I):
						if counter[entity] > 0:
							counter[entity] *= -1
						elif counter[entity] == 0:
							counter[entity] -= 1
						break

		# infobox fields
		for entity in patterns.keys():
			for field in patterns[entity]["fields"]:
				if field in extracted["data"]:
					counter[entity] += 1 if counter[entity] >= 0 else 0
			if "!fields" in patterns[entity]:
				for field in patterns[entity]["!fields"]:
					if field in extracted["data"]:
						if counter[entity] > 0:
							counter[entity] *= -1
						elif counter[entity] == 0:
							counter[entity] -= 1
						break

		return counter

	##
	# @brief deletes references, comments, etc. from a page content
	# @param page_content - string containing page_content
	# @return page content without reference tags, comments, etc...
	def remove_not_important(self, page_content):
		clean_content = page_content

		# remove comments
		clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)

		# remove references
		clean_content = re.sub(r"<ref[^<]*?/>", "", clean_content, flags=re.DOTALL)
		clean_content = re.sub(r"<ref(?:.*?)?>.*?</ref>", "", clean_content, flags=re.DOTALL)

		# remove {{efn ... }}, {{refn ...}}, ...
		clean_content = self.remove_ref_templates(clean_content)

		clean_content = re.sub(r"<nowiki/>", " ", clean_content, flags=re.DOTALL)
		#clean_content = re.sub(r"<.*?/?>", "", clean_content, flags=re.DOTALL)

		return clean_content

	##
	# @brief delete breaks of lines
	# @param page_content - string containing content of page
	# @return page content without breaks of lines
	def remove_breaks(self, page_content):
		# remove break lines
		clean_content = re.sub(r"<br\s*?/>", "  ", page_content, flags=re.DOTALL)
		clean_content = re.sub(r"<br>", "  ", clean_content, flags=re.DOTALL)

		return clean_content

	##
	# @brief replace breaks of lines by commas
	# @param page_content - string containing content of page
	# @return page content, where breaks of lines are replaced by commas
	def replace_breaks_by_commas(self, page_content):
		# remove break lines
		clean_content = re.sub(r"<br\s*?/>", ", ", page_content, flags=re.DOTALL)
		clean_content = re.sub(r"<br>", ", ", clean_content, flags=re.DOTALL)

		return clean_content

	##
	# @brief removes some references in {{}} brackets
	# @param content - page content
	@staticmethod
	def remove_ref_templates(content):
		# TODO: maybe not a good idea to remove all of them?
		# e.g.: you can extract langs from {{efn}} in https://en.wikipedia.org/wiki/Protectorate_of_Bohemia_and_Moravia
		patterns = [
			r"\{\{efn",
			r"\{\{refn",
			r"\{\{citation",
			r"\{\{notetag",
			r"\{\{snf",
			r"\{\{sfn",
			r"\{\{#tag:ref",
			r"\{\{ref label"
		]

		spans = []

		for p in patterns:
			match = re.finditer(p, content, flags=re.I)
			for m in match:
				start = m.span()[0]
				end = start
				indent = 0
				for c in content[start:]:
					if c == '{':
						indent += 1
					elif c == '}':
						indent -= 1
					end += 1
					if indent == 0:
						break
				spans.append((start, end))

		for span in sorted(spans, reverse=True):
			start, end = span
			# debug.log_message(f"removed: {content[start:end]}")
			content = content[:start] + content[end:]

		content = re.sub(r"[ \t]+", " ", content)

		return content

if __name__ == "__main__":
	wiki_extract = WikiExtract()

	wiki_extract.parse_args()
	wiki_extract.create_head_kb()
	wiki_extract.assign_version()
	wiki_extract.parse_xml_dump()
	wiki_extract.tracker.log()
