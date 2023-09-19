import glob
import sys
import unicodedata
from greek_normalisation.utils import convert_to_2019

def normalize_file(filename):
    try: 
        with open(filename, 'r+', encoding='utf-8') as f:
            file_contents = f.read()
            f.seek(0)
            f.write(convert_to_2019(file_contents))
            f.truncate()
    except:
        print('Error: ' + str(sys.exc_info()[0]))

# TO-DO - refactor this to pass in a directory from command line 
files_dir = r'C:\Users\Sarah McCuan\Documents\projects\ChambersGreekWar\text\\'
files_list = glob.glob(files_dir + '*.txt')

for file in files_list:
    normalize_file(file)
