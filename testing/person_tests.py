
import unittest, json, os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_person import EntPerson

from lang_modules.en.person_utils import PersonUtils as EnUtils
from lang_modules.cs.person_utils import PersonUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

def load_json(lang):
	d = dict()
	patterns_fpath = f"json/patterns_{lang}.json"
	try:
		with open(patterns_fpath, "r") as file:
			d = json.load(file)
	except OSError:
		exit(1)

	keywords = d["keywords"]
	identification = d["identification"]		
	return identification, keywords

class PersonTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(PersonTests, self).__init__(*args, **kwargs)
		
		_, self.keywords_en = load_json("en")
		_, self.keywords_cs = load_json("cs")
		
		self.person = EntPerson(
			"title", 
			"person", 
			"https://en.wikipedia.org/wiki/",
			{
				"data": {},
				"name": "infobox_name",
				"categories": [],
				"paragraph": "",
				"coords": "",
				"images": []
			},
			{},
			["redirects"],
			"sentence",
			self.keywords_en
		)
		self.person.core_utils = utils["en"]

	def change_keywords(self, lang=None):
		if lang == "cs":
			self.person.keywords = self.keywords_cs
		else:
			self.person.keywords = self.keywords_en
				
	def test_dates(self):
		self.change_keywords()		
		birth_values = [
			# en
			("1950", ("1950-??-??", "")),
			("{{Birth date|1936|06|08|mf=y}}", ("1936-06-08", "")),
			("{{Birth date and age|1947|5|6|mf=y}}", ("1947-05-06", "")),
			("{{Birth-date|October 24, 1919}}", ("1919-10-24", "")),
			("{{Birth-date and age|1 December 1968}}", ("1968-12-01", "")),
			("{{birth year and age|1969}}", ("1969-??-??", "")),
			("{{birth year|1959}}", ("1959-??-??", "")),
			("2 May 1956", ("1956-05-02", "")),
			("December 3, 1935", ("1935-12-03", "")),
			("{{b-da|26 November 1948}}", ("1948-11-26", "")),
			("16 November 42 BC", ("-42-11-16", "")),
			("24 December 3 BC", ("-3-12-24", "")),
			("9 June AD&nbsp;68 (aged 30)", ("68-06-09", "")),
			("15 January AD 69 (aged 70)", ("69-01-15", "")),
			("{{circa|lk=no|165}}", ("165-??-??", "")),
			("c. 258{{sfn|Leadbetter|pp=18–21}}{{sfn|Barnes|1982|p=37}}", ("258-??-??", "")),
			("''circa'' 280 BC", ("-280-??-??", "")),

			("change lang", "cs"),
			# cs
			("[[9. červen|9. června]] [[1640]]", ("1640-06-09", "")),
			("[[5. květen|5. května]] [[1705]] (64 let)", ("1705-05-05", "")),
			("[[listopad]] [[1165]]", ("1165-11-??", "")),
			("[[1278]]/[[1279]]{{nejisté datum|narození}}", ("1278-??-??/1279-??-??", "")),
			("{{datum narození|1368|02|14}}", ("1368-02-14", "")),
			("{{Datum narození a věk|1934|4|15}}", ("1934-04-15", "")),
			("[[25. říjen]] [[1949]] ({{Věk|1949|10|25}} let)", ("1949-10-25", "")),
			("[[21. květen|21. května]] [[120 př. n. l.]]", ("-0119-05-21", ""))
		]

		death_values = [
			# en
			("{{death date and age |1999|04|27 |1952|07|23}}", ("1952-07-23", "1999-04-27")),
			("{{Death-date and age|December 1, 1994|October 24, 1919}}", ("1919-10-24", "1994-12-01")),
			("{{d-da|28 June 1992|9 November 1936}}", ("1936-11-09", "1992-06-28")),
			
			("change lang", "cs"),
			#cs
			("{{datum úmrtí a věk|1437|12|09|1368|02|14}}", ("", "1437-12-09")),
			("{{Datum úmrtí a věk|1637|2|15|1578|7|9}}", ("", "1637-02-15")),
			("{{nowrap|{{Datum úmrtí a věk|2020|7|27|1925|9|19}}}}", ("", "2020-07-27"))
		]

		for i in birth_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.person.core_utils = utils[result]
				self.change_keywords(result)
				continue
			self.person.infobox_data["birth_date"] = value
			self.person.infobox_data["datum narození"] = value
			self.person.birth_date, self.person.death_date = self.person.core_utils.assign_dates(self.person)
			self.assertEqual(self.person.birth_date, result[0])
		
		self.person.lang = "en"
		self.person.core_utils = utils["en"]
		self.person.infobox_data["birth_date"] = ""
		self.person.infobox_data["datum narození"] = ""

		for i in death_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.person.core_utils = utils[result]
				self.change_keywords(result)
				continue
			self.person.infobox_data["death_date"] = value
			self.person.infobox_data["datum úmrtí"] = value
			self.person.birth_date, self.person.death_date = self.person.core_utils.assign_dates(self.person)
			self.assertEqual(self.person.birth_date, result[0])
			self.assertEqual(self.person.death_date, result[1])

	def test_places(self):
		self.change_keywords()
		infobox_values = [
			# en
			("Beijing, China", "Beijing, China"),
			("[[Gangtok, Sikkim|Gangtok]], [[Sikkim]], India", "Gangtok, Sikkim, India"),
			("[[Brooklyn]], New York, United States", "Brooklyn, New York, United States"),
			("[[San Francisco]], [[California]], [[United States of America|USA]]", "San Francisco, California, USA"),
			("[[Virginia]], United States [[File:Flag of the United States.svg|20px]]", "Virginia, United States"),
			("[[Belgrade]], [[Kingdom of Serbs, Croats and Slovenes]]{{small|(now [[Serbia]])}}", "Belgrade, Kingdom of Serbs, Croats and Slovenes(now Serbia)"),
			("[[Yerevan]], [[Armenian Soviet Socialist Republic|Armenian SSR]], {{nowrap|Soviet Union}}", "Yerevan, Armenian SSR, Soviet Union"),
			
			("change lang", "cs"),
			# cs
			("[[Benátky nad Jizerou]] {{Vlajka a název|Rakousko-Uhersko}}", "Benátky nad Jizerou Rakousko-Uhersko"),
			("{{flagicon|TCH}} [[Praha]], [[Československo]]", "TCH Praha, Československo"),
			("[[Zlín]] {{nowrap|{{flagicon|Protektorát Čechy a Morava}} [[Protektorát Čechy a Morava]]}}", "Zlín Protektorát Čechy a Morava Protektorát Čechy a Morava"),
			("[[Novo mesto]] [[Soubor: Flag of Yugoslavia (1918–1943).svg |20px]] [[Království Srbů, Chorvatů a Slovinců]]", "Novo mesto Království Srbů, Chorvatů a Slovinců"),
			("[[Královo Pole ]]  {{Vlajka a název|Rakousko-Uhersko}}", "Královo Pole Rakousko-Uhersko")
		]

		for i in infobox_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.person.core_utils = utils[result]
				self.change_keywords(result)
				continue
			self.person.infobox_data["birth_place"] = value
			self.person.infobox_data["místo narození"] = value
			self.person.assign_places()
			self.assertEqual(self.person.birth_place, result)

	def test_gender(self):
		self.change_keywords()
		infobox_values = [
			# en
			("male", "M"),
			("female", "F"),
			
			("change lang", "cs"),
			# cs
			("muž", "M"),
			("žena", "F")
		]

		categories = [
			# en
			("female authors", "F"),
			("female fictional characters", "F"),
			("male poets", "M"),
			("male scientists", "M"),
			
			("change lang", "cs"),
			# cs
			("muži", "M"),
			("ženy", "F")	
		]

		for i in infobox_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.change_keywords(result)
				continue
			self.person.infobox_data["gender"] = value
			self.person.infobox_data["pohlaví"] = value
			self.person.assign_gender()
			self.assertEqual(self.person.gender, result)

		for c in categories:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.change_keywords(result)
				continue
			self.person.categories = [c]
			self.person.assign_gender()
			self.assertEqual(self.person.gender, result)

	def test_jobs(self):
		self.change_keywords("cs")
		infobox_values = [
			# cs
			("režisér, scenárista, producent", "režisér|scenárista|producent"),
			("[[herec]], [[moderátor (profese)|moderátor]], [[komik]], [[bavič]], [[humorista]], [[tanečník]], [[baleťák]], [[zpěvák]], [[dabér]], [[scenárista]]", "herec|moderátor|komik|bavič|humorista|tanečník|baleťák|zpěvák|dabér|scenárista"),
			("[[zpěvák]], muzikálový herec a&nbsp;zpěvák", "zpěvák|muzikálový herec a zpěvák"),
			
			("change lang", "en"),
			# en
			("{{hlist | Computer programmer | businessperson}}", "Computer programmer|businessperson"),
			("[[Programmer]]; [[Politician]]", "Programmer|Politician"),
			("{{indented plainlist|\n* [[Invention|Inventor]]\n* [[Cryptography|Cryptographer]]}}", "Inventor|Cryptographer"),
			("{{ubl|[[Mad scientist|Scientist]]|Inventor|Leader of the Citadel (formerly)|Freedom fighter (formerly)}}", "Scientist|Inventor|Leader of the Citadel|Freedom fighter"),
			("{{unbulleted list|Scholar|Librarian |Poet |Inventor}}", "Scholar|Librarian|Poet|Inventor")
		]

		for i in infobox_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.change_keywords(result)
				continue
			self.person.infobox_data["occupation"] = value
			self.person.infobox_data["profese"] = value
			self.person.assign_jobs()
			self.assertEqual(self.person.jobs, result)	

	def test_nationality(self):
		self.change_keywords()
		infobox_values = [
			# en
			("{{flag|United States}}", "United States"),
			("[[United States|American]]", "American"),
			("[[flag|United States]]", "United States"),
			("Dreamlander, Maruvian", "Dreamlander|Maruvian"),
			("[[French people|French]]-[[Austrians|Austrian]]", "French|Austrian"),
			("British/Oceanian (in film)", "British|Oceanian"),
			
			("change lang", "cs"),
			# cs
			("{{flagicon|CRO}} [[Chorvati|chorvatká]]", "chorvatká"),
			("[[Češi|česká]]", "česká")
		]

		for i in infobox_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				self.change_keywords(result)
				continue
			self.person.infobox_data["nationality"] = value
			self.person.infobox_data["národnost"] = value
			self.person.assign_nationality()
			self.assertEqual(self.person.nationality, result)	

if __name__ == "__main__":
	unittest.main()