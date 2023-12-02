import markdown

# define header and footer html
HEADER = f"""\
    <!DOCTYPE html>
    <html lang="grc">
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css?family=Noto+Serif:400,700&amp;subset=greek,greek-ext" rel="stylesheet">
    <link href="style.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/alpheios-components@latest/dist/style/style-components.min.css">
    <title>The Greek War of Independence | Charles D. Chambers</title>
    </head>
    <body class="default">
    <div class="container alpheios-enabled" lang="grc">
    """
FOOTER = f"""\
    </p>
    </div>
    <footer>
        <p>This work is licensed under a <a href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.</p>
    </footer>
    </div>
    <script type="text/javascript" src="script.js"></script>
    </body>
    </html>
    """ 

def wrap(text_to_be_wrapped: str, tag: str, id = '', classes = [], lang = ''):
    if id != '':
        id = ' id=\"{}\"'.format(id)
    if lang != '':
        lang = ' lang=\"{}\"'.format(lang)
    if classes == []:
        classes = ''
    elif classes != []:
        temp = 'class=\"'
        for i in classes:
            temp += '{} '.format(i)
        classes = ' ' + temp.strip() + '\"'
    return '<{}{}{}{}>{}</{}>'.format(tag, id, classes, lang, text_to_be_wrapped,tag)

def wrap_sentence(sentence: str, id = ''):
    return(wrap(sentence, 'span', id, ['sentence']))

def wrap_paragraph(paragraph: str, id = ''):
    return(wrap(paragraph, 'p', id))

def wrap_chapter(chapter: str, id = ''):
    return(wrap(chapter, 'div', id, ['chapter', 'section']))

def wrap_chapter_heading(chapter_heading: str, id = ''):
    return(wrap(chapter_heading, 'h2', id, classes = ['section-title'], lang = 'en'))

def wrap_title(title: str, id = ''):
    return(wrap(title, 'h1', id, classes = ['title'], lang = 'en'))

body = ""

with open('text/chambers_w_headers.txt', 'r', encoding="utf-8") as f:
    text = f.read()
    lines = text.splitlines()
    chapters = []
    for i in range(len(lines)):
        line = lines[i]
        line_key = line[0:8]
        line_chapter = line[0:2]
        line_paragraph = line[3:5]
        line_sentence = line[6:8]
        line_txt = line[9:len(line)]
        if i == 0: # first line, title
            body += wrap_title(line_txt, line_key)
        elif i == 1: # handle first non-title line
            body += '\n <div class="chapter">\n'
            body += wrap_chapter_heading(line_txt, line_key)
        else: # every line but the first 2
            if line_paragraph == '00': # chapter headings
                body += '</p>\n</div>\n<div class="chapter">\n'
                body += wrap_chapter_heading(line_txt, line_key)
            else: # lines not title headings or chapter titles
                if line_sentence == '01': # first lines of paragraph
                    body += '\n<p>'
                body += wrap_sentence(line_txt, line_key) + ' '

print(body)
html = '\n'.join([HEADER, body, FOOTER])

with open('docs/chambers-txt.html', 'w', encoding="utf-8") as f:
    f.write(html)
