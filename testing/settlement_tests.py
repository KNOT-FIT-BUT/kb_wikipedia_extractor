
import unittest, json, os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_settlement import EntSettlement
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

class SettlementTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(SettlementTests, self).__init__(*args, **kwargs)
		_, self.keywords_en = load_json("en")
		_, self.keywords_cs = load_json("cs")
		self.entity = EntSettlement(
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

	def test_country(self):
		pass

if __name__ == "__main__":
	unittest.main()