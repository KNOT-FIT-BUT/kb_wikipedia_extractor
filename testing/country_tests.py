
import unittest, json, os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_country import EntCountry
from debugger import Debugger

from lang_modules.cs.core_utils import CoreUtils as CsCoreUtils
from lang_modules.en.core_utils import CoreUtils as EnCoreUtils

from lang_modules.cs.country_utils import CountryUtils as CsCountryUtils
from lang_modules.en.country_utils import CountryUtils as EnCountryUtils

core_utils = {
	"en": EnCoreUtils,
	"cs": CsCoreUtils
}

country_utils = {
	"en": EnCountryUtils,
	"cs": CsCountryUtils
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

class CountryTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(CountryTests, self).__init__(*args, **kwargs)
		
		_, self.keywords_en = load_json("en")
		_, self.keywords_cs = load_json("cs")

		self.entity = EntCountry(
			"title", 
			"country", 
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
	
	def change_keywords(self, lang=None):
		if lang == "cs":
			self.entity.keywords = self.keywords_cs
		else:
			self.entity.keywords = self.keywords_en

	def test_prefix(self):
		values = [
			(["developed country"], "country"),
			(["former countries"], "country:former"),

			("change lang", "cs"),
			(["krátce existující státy"], "country:former"),
			(["zaniklé státy"], "country:former"),
			(["zaniklé monarchie"], "country:former"),
			(["státy"], "country"),
		]

		for i in values:
			value, wanted = i
			if value == "change lang":
				self.entity.lang = wanted
				self.change_keywords(wanted)
				self.core_utils = core_utils[wanted]
				continue
			result = country_utils[self.entity.lang].assign_prefix(value)
			self.assertEqual(result, wanted)

if __name__ == "__main__":
	unittest.main()