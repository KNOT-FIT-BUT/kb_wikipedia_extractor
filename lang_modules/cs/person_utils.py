#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @file person_utils.py
# @brief cs specific preson utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re
from debugger import Debugger as debug
from lang_modules.cs.core_utils import CoreUtils
from libs.natToKB import *

class PersonUtils:
	##
	# @brief assigns prefix to the person entity
	#
	# person, person:fictional or person:group
	@staticmethod
	def assign_prefix(person):
		# prefix - fiktivní osoby
		# TODO: temp content? joining categories?
		content = "\n".join(person.categories)
		if (re.search(r"hrdinové\s+a\s+postavy\s+řecké\s+mytologie", content, re.I,) or 
			re.search(r"bohové", content, re.I) or 
			re.search(r"postavy", content, re.I)):			
			return "person:fictional" 

		# prefix - groups
		natToKB = NatToKB()
		nationalities = natToKB.get_nationalities()

		name_without_location = re.sub(r"\s+(?:ze?|of|von)\s+.*", "", person.title, flags=re.I)
		a_and_neighbours = re.search(r"((?:[^ ])+)\s+a(?:nd)?\s+((?:[^ ])+)", name_without_location)
		if a_and_neighbours:
			if (a_and_neighbours.group(1) not in nationalities or a_and_neighbours.group(2) not in nationalities):
				# else Kateřina Řecká a Dánská" is regular person
				return "person:group"
		
		return "person"

	##
	# @brief cs version of date extraction
	@classmethod
	def assign_dates(cls, person):
		birth_date = ""
		death_date = ""
		
		# Date of birth
		keys = ["datum narození", "datum_narození"]
		for key in keys:
			if key in person.infobox_data and person.infobox_data[key]:
				value = person.infobox_data[key]
				value = CoreUtils.del_redundant_text(value)
				birth_date = cls._convert_date(value, True)
				break

		# Date of death
		keys = ["datum úmrtí", "datum_úmrtí"]
		for key in keys:
			if key in person.infobox_data and person.infobox_data[key]:
				value = person.infobox_data[key]
				value = CoreUtils.del_redundant_text(value)
				death_date = cls._convert_date(value, False)
				break

		return (birth_date, death_date)

	##
	# @brief tries to extract dates and places from the first sentence
	@classmethod
	def extract_dates_and_places(cls, person):
		birth_date = ""
		death_date = ""
		birth_place = ""
		death_place = ""
		text = person.first_sentence

		# (* 2000)
		if not person.birth_date:
			rexp = re.search(r"\(\s*\*\s*(\d+)\s*\)", text)
			if rexp and rexp.group(1):
				birth_date = cls._convert_date(rexp.group(1), True)

		# (* 1. ledna 2000)
		if not person.birth_date:
			rexp = re.search(r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*\)", text)
			if rexp and rexp.group(1):
				birth_date = cls._convert_date(rexp.group(1), True)

		# (* 1. ledna 2000, Brno), (* 1. ledna 200 Brno, Česká republika)
		if not person.birth_date or not person.birth_place:
			rexp = re.search(
				r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])\s*(?![\-–—−])\)",
				text,
			)
			if rexp:
				if rexp.group(1) and not person.birth_date:
					birth_date = cls._convert_date(rexp.group(1), True)
				if rexp.group(2) and not person.birth_place:
					birth_place = cls.get_place(rexp.group(2))

		# (* 2000 – † 2018), (* 2000, Brno - † 2018 Brno, Česká republika)
		if (
			not person.birth_date
			or not person.death_date
			or not person.birth_place
			or not person.death_place
		):
			rexp = re.search(
				r"\(\s*(?:\*\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)",
				text,
			)
			if rexp:
				if rexp.group(1) and not person.birth_date:
					birth_date = cls._convert_date(rexp.group(1), True)
				if rexp.group(2) and not person.birth_place:
					birth_place = cls.get_place(rexp.group(2))
				if rexp.group(3) and not person.death_date:
					death_date = cls._convert_date(rexp.group(3), False)
				if rexp.group(4) and not person.death_place:
					death_place = cls.get_place(rexp.group(4))

		# (* 1. ledna 2000 – † 1. ledna 2018), (* 1. ledna 2000, Brno - † 1. ledna 2018 Brno, Česká republika)
		if (
			not person.birth_date
			or not person.death_date
			or not person.birth_place
			or not person.death_place
		):
			rexp = re.search(
				r"\(\s*(?:\*\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)",
				text,
			)
			if rexp:
				if rexp.group(1) and not person.birth_date:
					birth_date = cls._convert_date(rexp.group(1), True)
				if rexp.group(2) and not person.birth_place:
					birth_place = cls.get_place(rexp.group(2))
				if rexp.group(3) and not person.death_date:
					death_date = cls._convert_date(rexp.group(3), False)
				if rexp.group(4) and not person.death_place:
					death_place = cls.get_place(rexp.group(4))

		return (birth_date, death_date, birth_place, death_place)
	
	##
	# @brief Převádí místo narození/úmrtí osoby do jednotného formátu.
	# @param place - místo narození/úmrtí osoby (str)
	# @param is_birth - určuje, zda se jedná o místo narození, či úmrtí (bool)
	@staticmethod
	def get_place(place):
		place = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", place, flags=re.I)
		place = re.sub(
			r"{{(?:vjazyce2|cizojazyčně|audio|cj)\|.*?\|(.+?)}}",
			r"\1",
			place,
			flags=re.I,
		)
		place = re.sub(r"{{malé\|(.*?)}}", r"\1", place, flags=re.I)
		place = re.sub(r"{{.*?}}", "", place)
		place = re.sub(r"<br(?: /)?>", " ", place)
		place = re.sub(r"<.*?>", "", place)
		place = re.sub(
			r"\[\[(?:Soubor|File):.*?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)[^\]]*\]\]",
			"",
			place,
			flags=re.I,
		)
		place = re.sub(r"\d+\s*px", "", place, flags=re.I)
		place = re.sub(
			r"(?:(?:,\s*)?\(.*?věk.*?\)$|\(.*?věk.*?\)(?:,\s*)?)", "", place, flags=re.I
		)
		place = re.sub(r"\(.*?let.*?\)", "", place, flags=re.I)
		place = re.sub(r",{2,}", ",", place)
		place = re.sub(r"(\]\])[^,]", r"\1, ", place)
		place = CoreUtils.del_redundant_text(place)
		place = re.sub(r"[{}<>\[\]]", "", place)
		place = re.sub(r"\s+", " ", place).strip().strip(",")
		return place

	##
	# @brief Umožňuje provádět vlastní transformace aliasů entity do jednotného formátu.
	# @param alias - alternativní pojmenování entity (str)
	# TODO custom aliases?
	# @staticmethod
	# def custom_transform_alias(alias, data):
		
	# 	re_titles_religious = []
	# 	if data["infobox_name"] in ["křesťanský vůdce", "světec"]:
	# 		# https://cs.wikipedia.org/wiki/Seznam_zkratek_c%C3%ADrkevn%C3%ADch_%C5%99%C3%A1d%C5%AF_a_kongregac%C3%AD
	# 		# https://cs.qwe.wiki/wiki/List_of_ecclesiastical_abbreviations#Abbreviations_of_titles_of_the_principal_religious_orders_and_congregations_of_priests
	# 		# http://www.katolik.cz/otazky/ot.asp?ot=657
	# 		re_titles_religious = [
	# 			"A(?:\. ?)?(?:F|M)\.?",  # AF, AM
	# 			"A(?:\. ?)?(?:B(?:\. ?)?)?A\.?",  # AA, ABA
	# 			"A(?:\. ?)?C(?:\. ?)?S\.?",  # ACS
	# 			"A(?:\. ?)?M(?:\. ?)?B(?:\. ?)?V\.?",  # AMBV
	# 			"B\.?",  # B
	# 			"C(?:\. ?)?C\.?(?: ?G\.?)?",  # CC, CCG
	# 			"C(?:\. ?)?F(?:\. ?)?C\.?",  # CFC
	# 			"C(?:\. ?)?F(?:\. ?)?Ss(?:\. ?)?S\.?",  # CFSsS
	# 			"C(?:\. ?)?C(?:\. ?)?R(?:\. ?)?R(?:\. ?)?M(?:\. ?)?M\.?",  # CCRRMM
	# 			"C(?:\. ?)?(?:J(?:\. ?)?)?M\.?",  # CJM, CM
	# 			"C(?:\. ?)?M(?:\. ?)?F\.?",  # CMF
	# 			"C(?:\. ?)?M(?:\. ?)?S(?:\. ?)?Sp(?:\. ?)?S\.?",  # CMSSpS
	# 			"C(?:\. ?)?P\.?(?: ?P(?:\. ?)?S\.?)?",  # CP, CPPS
	# 			"Č(?:\. ?)?R\.?",  # ČR
	# 			"C(?:\. ?)?R(?:\. ?)?C(?:\. ?)?S\.?",  # CRCS
	# 			"C(?:\. ?)?R(?:\. ?)?I(?:\. ?)?C\.?",  # CRIC
	# 			"C(?:\. ?)?R(?:\. ?)?(?:L|M|T|V)\.?",  # CRL, CRM, CRT, CRV
	# 			"C(?:\. ?)?R(?:\. ?)?M(?:\. ?)?(?:D|I)\.?",  # CRMD, CRMI
	# 			"C(?:\. ?)?R(?:\. ?)?(?:S(?:\. ?)?)?P\.?",  # CRP, CRSP
	# 			"C(?:\. ?)?S(?:\. ?)?(?:B|C|J|P|V)\.?",  # CSB, CSC, CSJ, CSP, CSV
	# 			"C(?:\. ?)?S(?:\. ?)?C(?:\. ?)?D(?:\. ?)?I(?:\. ?)?J\.?",  # CSCDIJ
	# 			"C(?:\. ?)?S(?:\. ?)?S(?:\. ?)?E\.?",  # CSSE
	# 			"C(?:\. ?)?S(?:\. ?)?Sp\.?",  # CSSp
	# 			"C(?:\. ?)?Ss(?:\. ?)?(?:CC|Cc|R)\.?",  # CSsCC, CSsR
	# 			"C(?:\. ?)?S(?:\. ?)?T(?:\. ?)?F\.?",  # CSTF
	# 			"D(?:\. ?)?K(?:\. ?)?L\.?",  # DKL
	# 			"D(?:\. ?)?N(?:\. ?)?S\.?",  # DNS
	# 			"F(?:\. ?)?D(?:\. ?)?C\.?",  # FDC
	# 			"F(?:\. ?)?M(?:\. ?)?A\.?",  # FMA
	# 			"F(?:\. ?)?M(?:\. ?)?C(?:\. ?)?S\.?",  # FMCS
	# 			"F(?:\. ?)?M(?:\. ?)?D(?:\. ?)?D\.?",  # FMDD
	# 			"F(?:\. ?)?S(?:\. ?)?C(?:\. ?)?I\.?",  # FSCI
	# 			"F(?:\. ?)?S(?:\. ?)?P\.?",  # FSP
	# 			"I(?:\. ?)?B(?:\. ?)?M(?:\. ?)?V\.?",  # IBMV
	# 			"Inst(?:\. ?)?Char\.?",  # Inst. Char.
	# 			"I(?:\. ?)?Sch\.?",  # ISch
	# 			"I(?:\. ?)?S(?:\. ?)?P(?:\. ?)?X\.?",  # ISPX
	# 			"I(?:\. ?)?S(?:\. ?)?S(?:\. ?)?M\.?",  # ISSM
	# 			"K(?:\. ?)?M(?:\. ?)?B(?:\. ?)?M\.?",  # KMBM
	# 			"K(?:\. ?)?S(?:\. ?)?H\.?",  # KSH
	# 			"K(?:\. ?)?S(?:\. ?)?N(?:\. ?)?S\.?",  # KSNS
	# 			"(?:L|M|O|S)(?:\. ?)?C\.?",  # LC, MC, OC, SC
	# 			"M(?:\. ?)?I(?:\. ?)?C\.?",  # MIC
	# 			"N(?:\. ?)?Id\.?",  # MId
	# 			"M(?:\. ?)?S\.?(?: ?(?:C|J)\.?)?",  # MS, MSC, MSJ
	# 			"N(?:\. ?)?D\.?",  # ND
	# 			"O(?:\. ?)?(?:Camald|Carm|Cart|Cist|Cr|Crucig|F|H|M|Melit|Merced|P|Praed|Praem|T|Trinit)\.?",  # OCamald, OCarm, OCart, OCist, OCr, OCrucig, OF, OH, OM, OMelit, OMerced, OP, OPraed, OPraem, OT, OTrinit
	# 			"O(?:\. ?)?C(?:\. ?)?(?:C|D|R)\.?",  # OCC, OCD, OCR
	# 			"O(?:\. ?)?C(?:\. ?)?S(?:\. ?)?O\.?",  # OCSO
	# 			"O(?:\. ?)?F(?:\. ?)?M\.?(?: ?(?:Cap|Conv|Rec)\.?)?",  # OFM, OFM Cap., OFM Conv., OFM Rec.
	# 			"O(?:\. ?)?M(\. ?)?(?:C|I)\.?",  # OMC, OMI
	# 			"O(?:\. ?)?(?:F(\. ?)?)?M(\. ?)?Cap\.?",  # OM Cap. OFM Cap.
	# 			"O(?:\. ?)?S(?:\. ?)?(?:A|B|C|E|F|H|M|U)\.?",  # OSA, OSB, OSC, OSE, OSF, OSH, OSM, OSU
	# 			"O(?:\. ?)?S(?:\. ?)?B(\. ?)?M\.?",  # OSBM
	# 			"O(?:\. ?)?S(?:\. ?)?C(\. ?)?(?:Cap|O)\.?",  # OSC Cap., OSCO
	# 			"O(?:\. ?)?S(?:\. ?)?F(?:\. ?)?(?:C|S)\.?",  # OSFC, OSFS
	# 			"O(?:\. ?)?S(?:\. ?)?F(\. ?)?Gr\.?",  # OSFGr
	# 			"O(?:\. ?)?Ss(?:\. ?)?C\.?",  # OSsC
	# 			"O(?:\. ?)?V(?:\. ?)?M\.?",  # OVM
	# 			"P(?:\. ?)?D(?:\. ?)?D(\. ?)?M\.?",  # PDDM
	# 			"P(?:\. ?)?O\.?",  # PO
	# 			"P(?:\. ?)?S(?:\. ?)?(?:M|S)\.?",  # PSM, PSS
	# 			"R(?:\. ?)?G(?:\. ?)?S\.?",  # RGS
	# 			"S(?:\. ?)?(?:A|J|S)(?:\. ?)?C\.?",  # SAC, SJC, SSC
	# 			"S(?:\. ?)?C(?:\. ?)?(?:B|H|M)\.?",  # SCB, SCH, SCM
	# 			"S(?:\. ?)?C(?:\. ?)?S(\. ?)?C\.?",  # SCSC
	# 			"S(?:\. ?)?D(?:\. ?)?(?:B|J|S)\.?",  # SDB, SDJ, SDS
	# 			"Sch(?:\. ?)?P\.?",  # SchP
	# 			"(?:S|T)(?:\. ?)?(?:I|J)\.?",  # SI, SJ, TI, TJ
	# 			"S(?:\. ?)?(?:P(?:\. ?)?)?M\.?",  # SM, SPM
	# 			"S(?:\. ?)?M(?:\. ?)?F(?:\. ?)?O\.?",  # SMFO
	# 			"S(?:\. ?)?M(?:\. ?)?O(?:\. ?)?M\.?",  # SMOM
	# 			"S(?:\. ?)?(?:P|Praem)\.?",  # SP, SPraem
	# 			"S(?:\. ?)?S(?:\. ?)?J\.?",  # SSJ
	# 			"S(?:\. ?)?S(?:\. ?)?N(?:\. ?)?D\.?",  # SSND
	# 			"S(?:\. ?)?(?:S|T)(?:\. ?)?S\.?",  # SSS, STS
	# 			"S(?:\. ?)?V\.?(?: ?D\.?)?",  # SV, SVD
	# 		]
	# 	# u titulů bez teček je třeba kontrolova mezeru, čárku nebo konec (například MA jinak vezme následující příjmení začínající "Ma..." a bude toto jméno považovat za součást předchozího)
	# 	re_titles_civil = [
	# 		r"J[rn]\.?",
	# 		"Sr\.?",
	# 		"ml(?:\.|adší)?",
	# 		"st(?:\.|arší)?",
	# 		"jun(\.|ior)?",
	# 		"[PT]h(\.\s?)?D\.?",
	# 		"MBA",
	# 		"M\.?A\.?",
	# 		"M\.?S\.?",
	# 		"M\.?Sc\.?",
	# 		"CSc\.",
	# 		"D(?:\.|r\.?)Sc\.",
	# 		"[Dd]r\. ?h\. ?c\.",
	# 		"DiS\.",
	# 		"CC",
	# 	]
	# 	#                 v---- need to be space without asterisk - with asterisk the comma will be replaced
	# 	alias = re.sub(
	# 		r", (?!("
	# 		+ "|".join(re_titles_civil + re_titles_religious)
	# 		+ r")(\.|,| |$))",
	# 		"|",
	# 		alias,
	# 		flags=re.I,
	# 	)
	# 	alias = regex.sub(
	# 	    r"(?<=^|\|)\p{Lu}\.(?:\s*\p{Lu}\.)+(\||$)", "\g<1>", alias
	# 	)  # Elimination of initials like "V. H." (also in infobox pseudonymes, nicknames, ...)

	# 	return alias

	##
	# @brief Zpracuje a konvertuje datum narození/úmrtí osoby do jednotného formátu.
	# @param date - datum narození/úmrtí osoby (str)
	# @param is_birth - určuje, zda se jedná o datum narození, či úmrtí (bool)
	# @return Datum narození/úmrtí osoby v jednotném formátu. (str)
	@classmethod
	def _convert_date(cls, date, is_birth):
		# detekce př. n. l.
		date_bc = True if re.search(r"př\.?\s*n\.?\s*l\.?", date, re.I) else False

		# datum před úpravou
		orig_date = date[:]

		# odstranění přebytečného textu
		date = date.replace("?", "").replace("~", "")
		date = re.sub(r"{{(?!\s*datum|\s*julgreg)[^}]+}}", "", date, flags=re.I)
		date = re.sub(r"př\.\s*n\.\s*l\.", "", date, flags=re.I)

		# staletí - začátek
		date = cls._subx(
			r".*?(\d+\.?|prvn.|druh.)\s*(?:pol(?:\.|ovin.))\s*(\d+)\.?\s*(?:st(?:\.?|ol\.?|oletí)).*",
			lambda x: cls._regex_date(x, 0),
			date,
			flags=re.I,
		)

		date = cls._subx(
			r".*?(\d+)\.?\s*(?:až?|[\-–—−/])\s*(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
			lambda x: cls._regex_date(x, 1),
			date,
			flags=re.I,
		)

		date = cls._subx(
			r".*?(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
			lambda x: cls._regex_date(x, 2),
			date,
			flags=re.I,
		)
		# staletí - konec

		# data z šablon - začátek
		if is_birth:
			date = cls._subx(
				r".*?{{\s*datum[\s_]+narození\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
				lambda x: cls._regex_date(x, 3),
				date,
				flags=re.I,
			)
		else:
			date = cls._subx(
				r".*?{{\s*datum[\s_]+úmrtí\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
				lambda x: cls._regex_date(x, 3),
				date,
				flags=re.I,
			)
		date = cls._subx(
			r".*?{{\s*JULGREGDATUM\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^}]*}}.*",
			lambda x: cls._regex_date(x, 4),
			date,
			flags=re.I,
		)
		# data z šablon - konec

		# data napsaná natvrdo - začátek
		date = cls._subx(
			r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
			lambda x: cls._regex_date(x, 8),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\s*(?:či|až?|nebo|[\-–—−/])\s*(\d+).*",
			lambda x: cls._regex_date(x, 5),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+).*",
			lambda x: cls._regex_date(x, 4),
			date,
		)
		date = cls._subx(
			r".*?((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
			lambda x: cls._regex_date(x, 9),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+).*",
			lambda x: cls._regex_date(x, 7),
			date,
			flags=re.I,
		)
		date = cls._subx(r".*?(\d{1,4}).*", lambda x: cls._regex_date(x, 6), date)
		# data napsaná natvrdo - konec

		# odstranění zdvojených bílých znaků a jejich převod na mezery
		date = cls._subx(r"\s+", " ", date).strip()

		# odstranění nezkonvertovatelných dat
		date = "" if orig_date == date else date

		# převod na formát data před naším letopočtem - začátek
		if date and date_bc:
			rexp = re.search(r"^([\d?]{4})-([\d?]{2})-([\d?]{2})$", date)
			if rexp and rexp.group(1):
				if rexp.group(1) != "????":
					bc_year = (
						"-" + str(int(rexp.group(1)) - 1).zfill(4)
						if rexp.group(1) != "0001"
						else "0000"
					)
					date = "{}-{}-{}".format(bc_year, rexp.group(2), rexp.group(3))
			else:
				rexp = re.search(
					r"^([\d?]{4})-([\d?]{2})-([\d?]{2})/([\d?]{4})-([\d?]{2})-([\d?]{2})$",
					date,
				)
				if rexp and rexp.group(1) and rexp.group(4):
					if rexp.group(1) != "????" and rexp.group(4) != "????":
						yr1, yr2 = int(rexp.group(1)), int(rexp.group(4))
						if (
							yr1 < yr2
						):  # prohození hodnot, pokud je první rok menší než druhý
							yr1, yr2 = yr2, yr1
						bc_year1 = "-" + str(yr1 - 1).zfill(4) if yr1 != 1 else "0000"
						bc_year2 = "-" + str(yr2 - 1).zfill(4) if yr2 != 1 else "0000"
						date = "{}-{}-{}/{}-{}-{}".format(
							bc_year1,
							rexp.group(2),
							rexp.group(3),
							bc_year2,
							rexp.group(6),
							rexp.group(6),
						)
		# převod na formát data před naším letopočtem - konec

		return date

	##
	# @brief Převádí předaný match object na jednotný formát data dle standardu ISO 8601.
	# @param match_obj  - match object (MatchObject)
	# @param match_type - určuje, jaký typ formátu se má aplikovat (int)
	# @return Jednotný formát data. (str)
	@classmethod
	def _regex_date(cls, match_obj, match_type):
		
		if match_type == 0:
			f = "{:04d}-??-??/{:04d}-??-??"
			if re.search(r"1\.?|prvn.", match_obj.group(1), re.I):
				f = f.format(
					(int(match_obj.group(2)) - 1) * 100 + 1,
					int(match_obj.group(2)) * 100 - 50,
				)
			else:
				f = f.format(
					(int(match_obj.group(2)) - 1) * 100 + 51,
					int(match_obj.group(2)) * 100,
				)
			return f

		if match_type == 1:
			f = "{:04d}-??-??/{:04d}-??-??"
			return f.format(
				(int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(2)) * 100
			)

		if match_type == 2:
			f = "{:04d}-??-??/{:04d}-??-??"
			return f.format(
				(int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(1)) * 100
			)

		if match_type == 3:
			f = "{}-{}-{}"
			year = "????" if not match_obj.group(1) else match_obj.group(1).zfill(4)
			month = "??" if not match_obj.group(2) else match_obj.group(2).zfill(2)
			day = "??" if not match_obj.group(3) else match_obj.group(3).zfill(2)
			return f.format(year, month, day)

		if match_type == 4:
			f = "{}-{}-{}"
			return f.format(
				match_obj.group(3).zfill(4),
				match_obj.group(2).zfill(2),
				match_obj.group(1).zfill(2),
			)

		if match_type == 5:
			return "{}-??-??/{}-??-??".format(
				match_obj.group(1).zfill(4), match_obj.group(2).zfill(4)
			)

		if match_type == 6:
			return "{}-??-??".format(match_obj.group(1).zfill(4))

		if match_type == 7:
			f = "????-{}-{}"
			return f.format(
				cls._get_cal_month(match_obj.group(2)), match_obj.group(1).zfill(2)
			)

		if match_type == 8:
			f = "{}-{}-{}"
			return f.format(
				match_obj.group(3).zfill(4),
				cls._get_cal_month(match_obj.group(2)),
				match_obj.group(1).zfill(2),
			)

		if match_type == 9:
			f = "{}-{}-??"
			return f.format(
				match_obj.group(2).zfill(4), cls._get_cal_month(match_obj.group(1))
			)

	##
	# @brief Převádí název kalendářního měsíce na číselný tvar.
	# @param month - název měsíce (str)
	# @return Číslo kalendářního měsíce na 2 pozicích, jinak ??. (str)
	@staticmethod
	def _get_cal_month(month):
		cal_months_part = [
			"led",
			"únor",
			"břez",
			"dub",
			"květ",
			"červ",
			"červen",
			"srp",
			"září",
			"říj",
			"listopad",
			"prosin",
		]

		for idx, mon in enumerate(cal_months_part, 1):
			if mon in month.lower():
				if (
					idx == 6 and "c" in month
				):  # v případě špatné identifikace června a července v některých pádech
					return "07"
				return str(idx).zfill(2)

		return "??"

	##
	# @brief Vykonává totožný úkon jako funkce sub z modulu re, ale jen v případě, že nenarazí na datum ve standardizovaném formátu.
	# @param pattern - vzor (str)
	# @param repl - náhrada (str)
	# @param string - řetězec, na kterém má být úkon proveden (str)
	# @param count - počet výskytů, na kterých má být úkon proveden (int)
	# @param flags - speciální značky, které ovlivňují chování funkce (int)
	@staticmethod
	def _subx(pattern, repl, string, count=0, flags=0):
		if re.match(r"[\d?]+-[\d?]+-[\d?]+", string):
			return string
		return re.sub(pattern, repl, string, count, flags)
