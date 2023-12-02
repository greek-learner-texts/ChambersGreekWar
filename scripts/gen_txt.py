# This script takes the Chambers markdown & parses it to create
# a txt file in the greek-learners-texts format

import sys
from pathlib import Path 

# opens markdown, returns a dict
# key is the line id, value is the sentence itself
def parse_md_with_headers(md_filename):
    try: 
        with open(md_filename, 'r+', encoding='utf-8') as f:
            raw_txt = f.read()
            section_index = 0
            paragraph_index = 1
            line_dict = {}
            for line in raw_txt.splitlines():
                line = line.strip()
                if (line[0:3] == '###'): # section headings
                    line = line[4:len(line)]
                    section_index += 1
                    paragraph_index = 1 # reset 
                    line_dict[str(section_index).rjust(2,'0') + '.00.00'] = line
                elif (line[0:2] == '##' or line == ''): # ignore part headings, extra blank lines
                    continue
                elif (line[0:1] == '#'): # handle book title
                    line = line[2:len(line)]
                    line_dict['00.00.00'] = line
                else: # parsing logic for paragraphs - should be only thing left
                    sentences = line.split('.')
                    sentence_index = 1
                    for sentence in sentences:
                        if (sentence == ''):
                            break
                        else:
                            sentence = sentence.strip() + '.' # add back periods
                            key = str(section_index).rjust(2,'0')+ '.' + str(paragraph_index).rjust(2,'0')+ '.' + str(sentence_index).rjust(2,'0')
                            line_dict[key] = sentence
                            sentence_index += 1
                    paragraph_index += 1
            return(line_dict) 
    except:
        print('Error: ' + str(sys.exc_info()[0]))

def parse_md_no_headers(md_filename):
    try: 
        with open(md_filename, 'r+', encoding='utf-8') as f:
            raw_txt = f.read()
            section_index = 0
            paragraph_index = 1
            line_dict = {}
            for line in raw_txt.splitlines():
                line = line.strip()
                if (line[0:3] == '###'): # section headings
                    section_index += 1
                    paragraph_index = 1 # reset 
                    # line_dict[str(section_index).rjust(2,'0') + '.00.00'] = line
                elif (line[0:2] == '##' or line == ''): # ignore part headings, extra blank lines
                    continue
                elif (line[0:1] == '#'): # handle book title
                    # line_dict['00.00.00'] = line
                    continue
                else: # parsing logic for paragraphs - should be only thing left
                    sentences = line.split('.')
                    sentence_index = 1
                    for sentence in sentences:
                        if (sentence == ''):
                            break
                        else:
                            sentence = sentence.strip() + '.' # add back periods
                            key = str(section_index).rjust(2,'0')+ '.' + str(paragraph_index).rjust(2,'0')+ '.' + str(sentence_index).rjust(2,'0')
                            line_dict[key] = sentence
                            sentence_index += 1
                    paragraph_index += 1
            return(line_dict) 
    except:
        print('Error: ' + str(sys.exc_info()[0]))

def gen_txt_with_headers(md_filename, txt_filename):
    line_dict = parse_md_with_headers(md_filename)
    try: 
        # write out dict to txt file 
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.seek(0)
            for key, sentence in line_dict.items():
                f.write(key + ' ' + sentence + '\n')
            f.truncate()
    #except:
        #print('Error: ' + str(sys.exc_info()[0]))
    except ValueError as error:
        print(str(error))

def gen_txt_no_headers(md_filename, txt_filename):
    line_dict = parse_md_no_headers(md_filename)
    try: 
        # write out dict to txt file 
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.seek(0)
            for key, sentence in line_dict.items():
                f.write(key + ' ' + sentence + '\n')
            f.truncate()
    #except:
        #print('Error: ' + str(sys.exc_info()[0]))
    except ValueError as error:
        print(str(error))

# relative path logic
chambers_path = Path(__file__).parent.parent
md_file_path = (chambers_path / 'drafts\\chambers_ocr.md').resolve()

no_headers_txt_file_path = (chambers_path / 'text\\chambers.txt').resolve()
headers_txt_file_path = (chambers_path / 'text\\chambers_w_headers.txt').resolve()

gen_txt_no_headers(md_file_path, no_headers_txt_file_path)
gen_txt_with_headers(md_file_path, headers_txt_file_path)