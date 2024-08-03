
def fix():

	line_numbers = []

	with open("bad_lines.log", "r") as f:
		for line in f:
			if line.startswith("Bad line"):
				number = line.split(" ")[2]
				line_numbers.append(int(number)-1)

	line_numbers.sort(reverse=True)

	lines = []

	with open("kb", "r") as f:
		lines = f.readlines()

	with open("kb_new", "w") as f:
		while len(line_numbers) != 0:
			index = line_numbers[0] 
			if index < len(lines):
				print(f"removing line {index}")
				lines.pop(index)
			else:
				print(f"line {index} not found")
			line_numbers.pop(0)
		f.writelines(lines)

if __name__ == "__main__":
	fix()