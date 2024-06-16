import glob
import sys
from greek_normalisation.utils import convert_to_2019, nfc
from text_validator.main import validate
from pathlib import Path 

def normalize_file(filename):
    try: 
        with open(filename, 'r+', encoding='utf-8') as f:
            file_contents = f.read()
            f.seek(0)
            f.write(nfc(convert_to_2019(file_contents)))
            f.truncate()
    except:
        print('Error: ' + str(sys.exc_info()[0]))

# relative path logic
# chambers_path = Path(__file__).parent.parent
# files_dir = (chambers_path / 'text\\').resolve()
# files_list = glob.glob(str(files_dir) + '*.txt')

# instead of using the list above and potentially messing up in-progress files, 
# it's easier to just individually specify what we want normalized: 

files_list = ['text/chambers_w_headers.txt', 'text/chambers.txt', 'docs/greek_english_vocab.html', 'docs/greekwar.html', 'docs/index.html']

for file in files_list:
    normalize_file(file)