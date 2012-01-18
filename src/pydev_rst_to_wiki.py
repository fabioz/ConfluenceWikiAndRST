import os
from rst_2_wiki import ConvertRstToWiki


if __name__ == '__main__':
    base = r'W:/pydev/plugins/com.python.pydev.docs/'
    for filename in ('manual_101_install.rst','manual_101_interpreter.rst',):
        with file(os.path.join(base, 'merged_homepage', filename), 'r') as f:
            contents = f.read()
            
            wiki_contents = ConvertRstToWiki(contents)
            converted = wiki_contents.Convert()
            path = os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents')
            if not os.path.exists(path):
                os.makedirs(path)
            with file(os.path.join(path, filename+'.wiki'), 'w') as out:
                out.write(converted)
            
        