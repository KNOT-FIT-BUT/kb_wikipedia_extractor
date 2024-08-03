
import unittest, json, os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_country import EntCountry
from debugger import Debugger

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

class CoreTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(CoreTests, self).__init__(*args, **kwargs)
		
		_, self.keywords_en = load_json("en")
		_, self.keywords_cs = load_json("cs")

		self.entity = EntCountry(
			"title", 
			"core", 
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

	def test_area(self):
		self.change_keywords()
		km_values = [
			("0.5", "0.5"),
			("0,5", "0.5"),
			("&nbsp; 0,5 {{nowrap|something}} (ref: 2016 messurements)", "0.5"),
			("1 000 000", "1000000"),
			("1,000,000", "1000000"),
			("10,000,5", "10000.5")
		]

		for i in km_values:
			value, wanted = i
			self.entity.infobox_data["area_km2"] = value
			result = self.entity.assign_area()
			self.assertEqual(result, wanted)
		self.entity.infobox_data["area_km2"] = ""

		sqmi_values = [
			("10", "25.9"),
			("20", "51.8")
		]

		for i in sqmi_values:
			value, wanted = i
			self.entity.infobox_data["area_sq_mi"] = value
			result = self.entity.assign_area()
			self.assertEqual(result, wanted)
		self.entity.infobox_data["area_sq_mi"] = ""

		values = [
			("{{convert|10|km2|sqmi}}", "10"),
			("{{cvt|10|km2|sqmi}}", "10"),
			("10 km2", "10"),
			("10km2", "10"),
		]

		for i in values:
			value, wanted = i
			self.entity.infobox_data["area"] = value
			result = self.entity.assign_area()
			self.assertEqual(result, wanted)

	def test_population(self):
		self.change_keywords()
		values = [
			("10", "10"),
			("10 &nbsp; (something)", "10"),
			("{{nowrap|10|20px}}", "10"),
			("{{circa|10}}", "10"),
			("uninhabited", "0"),
			("neobydlený", "0"),
			("bez obyvatel", "0"),
			("10,000", "10000"),
			("10 000", "10000")
		]

		for i in values:
			value, wanted = i
			self.entity.infobox_data["population"] = value
			result = self.entity.assign_population()
			self.assertEqual(result, wanted)

	def test_coords(self):
		self.change_keywords()
		values = [
			("{{coord|51|30|N|0|7|W|type:city|display=inline}}", ("51.5", "-0.11667")),
			("{{coord|51|30|S|0|7|E|type:city|display=inline}}", ("-51.5", "0.11667")),
			("{{coord|1|N|2|W|type:city|display=inline}}", ("1.0", "-2.0")),
			("{{coord|1|2|3|N|2|3|4|W|type:city|display=inline}}", ("1.13333", "-2.18333")),
			("coords missing", ("", "")),
			("aaa", ("", "")),
		]

		for i in values:
			value, wanted = i
			self.entity.infobox_data["coordinates"] = value
			result = self.entity.core_utils.assign_coordinates(self.entity)
			self.assertEqual(result[0], wanted[0])
			self.assertEqual(result[1], wanted[1])

if __name__ == "__main__":
	unittest.main()