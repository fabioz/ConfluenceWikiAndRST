import os
from rst_2_wiki import ConvertRstToWiki


if __name__ == '__main__':
    base = r'W:/pydev/plugins/com.python.pydev.docs/'
    
    import sys
    sys.path.append(r'W:/pydev/plugins/com.python.pydev.docs/merged_homepage/scripts')
    import build_merged #@UnresolvedImport
    
    manual_adv = build_merged.manualAdv
    manual_101 = build_merged.manual101
    
    all = manual_101 + manual_adv
    
    for template, filename, title in manual_adv:
        target = os.path.join(base, 'merged_homepage', filename+'.rst')
        if not os.path.exists(target):
            target = os.path.join(base, 'merged_homepage', filename+'.contents.rst')
            if not os.path.exists(target):
                
                target = os.path.join(base, 'merged_homepage', filename+'.wiki')
                if not os.path.exists(target):
                    print >> sys.stderr, "Skipping: ", title, '\t\t', target
                    continue
        
        with file(target, 'r') as f:
            print title,'\t\t', filename
            try:
                if target.endswith('.wiki'):
                    converted = f.read()
                else:
                    contents = f.read()
                    wiki_contents = ConvertRstToWiki(contents)
                    converted = wiki_contents.Convert()
                    
                path = os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents')
                if not os.path.exists(path):
                    os.makedirs(path)
                    
                for _, repl_name, repl_title in all:
                    repl_name += '.html'
                    converted = converted.replace(repl_name, 'PyDev '+repl_title)
                    
                with file(os.path.join(path, filename+'.wiki'), 'w') as out:
                    out.write(converted)
            except:
                print >> sys.stderr, 'Error converting: ', filename
                raise
            
        