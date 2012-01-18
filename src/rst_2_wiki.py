#Convert rst content to confluence wiki content

import os.path 
import re


#=======================================================================================================================
# ConvertRstToWiki
#=======================================================================================================================
class ConvertRstToWiki(object):
    
    def __init__(self, contents):
        self._content = contents
        self._lines = contents.splitlines()
        self._re_link_definition = re.compile(r'(\s)*\.\.(\s)*_(`)?((\w|\s|:|/|\.)*)(`)?:(.*)')
        self._re_link_definition1 = re.compile(r'(\s)*\.\.(\s)*_(`)((\w|\s|:|/|\.)*)(`):(.*)')
        self._re_link_use = re.compile(r'`((\w|\s|:|/|\.)*)`_')
        self._re_start_image = re.compile(r'\s*\.\.(\s)*image\:\:(\s)*(.*)')
        self._re_start_sourcecode = re.compile(r'\s*\.\.(\s)*sourcecode\:\:(\s)*(.*)')
        self._links = {}
        self._line_count = len(self._lines)
        self._images_prefix = 'http://pydev.org/'
        self._finishing_operations = []
        
    
    def _ContainsOnlySameChar(self, line):
        stripped = line.strip()
        if len(stripped) == 0:
            return False
        old = None
        for c in stripped:
            if old is not None:
                if old != c:
                    return False
            old = c
        return True
    
    
    def _GetFirstNonWhiteSpaceIndex(self, line):
        for i in xrange(len(line)):
            if line[i] != ' ' and line[i] != '\t':
                return i
        return -1
    
    
    def _SkipCommentBlock(self, i):
        line = self._lines[i]
        ignore_until_indentation_lower_than = self._GetFirstNonWhiteSpaceIndex(line)
        
        while i < self._line_count - 1:
            i += 1
            line = self._lines[i]
            indentation = self._GetFirstNonWhiteSpaceIndex(line)
            if indentation == -1:
                continue
            elif indentation > ignore_until_indentation_lower_than:
                continue
            else:
                return i - 1
            
        return i
    

    def _HandleRawBlock(self, i):
        start = i
        end = self._SkipCommentBlock(i)
        
        line = '{quote}\n'
        for i in xrange(start+1, end+1):
            line += '\n' +self._lines[i]
        line += '\n{quote}'
        
        self._output_lines.append(line)
        return end
    
    

    def _HandleImage(self, i):
        start = i
        end = self._SkipCommentBlock(i)
        
        match = self._re_start_image.match(self._lines[i])
        url = self._images_prefix + match.group(3).strip()
        self._output_lines.append('!%s|border=1!' % url)
        
        return end
        
    def _HandleSourceCode(self, i):
        start = i
        end = self._SkipCommentBlock(i)
        
        line = '{code:language=python}\n'
        for i in xrange(start+1, end+1):
            line += '\n' +self._lines[i]
        line += '\n{code}'
        
        self._output_lines.append(line)
        return end
        
            
    
    def _HandleTable(self, i):
        start = i
        end = self._SkipCommentBlock(i)
        
        
#        match = self._re_start_image.match(self._lines[i])
#        url = self._images_prefix+match.group(3).strip()
#        self._output_lines.append('!%s|border=1!' % url)
        
        content = '||%s' % self._lines[i].strip()[1:] #Remove the initial ':'
        #Contents of the image (ignored for now).
        for i in xrange(start + 1, end + 1):
            line = self._lines[i]
            stripped = line.strip()
            if len(stripped) == 0:
                continue
            content += ('|' + self._ConvertLineLinks(line))
        
        content += '||'
        self._output_lines.append(content)
        
        return end
    
    
    def _CreateAnchorCallable(self, group, link):
        def FinishAnchor(content):
            return content.replace(link, '{anchor: %s}%s' % (group, group))
        self._finishing_operations.append(FinishAnchor)
    
    
    def _ConvertLineLinks(self, line):
        chars = list(line)
        match = self._re_link_use.search(line)
        while match is not None:
            group = match.group(1).strip()
            try:
                link = self._links[group]
            except KeyError:
                inner_link = '_`%s`' % group
                if inner_link in self._content:
                    lst = list('[#' + group + ']')
                    chars[match.start():match.end()] = lst
                    
                    #Redo the line for the next search
                    line = ''.join(chars)
                    match = self._re_link_use.search(line, match.start() + len(lst))
                    self._CreateAnchorCallable(group, inner_link)
                    
                else:
                    raise AssertionError('Could not find: %s in %s.\nFor line: %s' % (group, self._links, line))
            else:
                lst = list('[' + group + '|' + link + ']')
                chars[match.start():match.end()] = lst
                
                #Redo the line for the next search
                line = ''.join(chars)
                match = self._re_link_use.search(line, match.start() + len(lst))
        return line
    

    
    
    def Convert(self):
        self._output_lines = []
        
        i = -1
        while i < self._line_count - 1:
            i += 1
            line = self._lines[i]
            
            if line.strip() == '.. contents::':
                continue
            
            match = self._re_link_definition.match(line)
            if match is not None:
                if '`' in line:
                    match = self._re_link_definition1.match(line)
                    groups = match.groups()
                    key = groups[3].strip()
                    val = groups[6].strip()
                    if key.startswith('`'):
                        key = key[1:]
                    if key.endswith('`'):
                        key = key[:-1]
                else:
                    try:
                        _, key, val = line.split()
                    except:
                        raise AssertionError('Wrong format for link (should probably have surrounding char: >>`<<): %s' % (line,))
                    key = key[1:-1] #Remove _***:
                    
                self._links[key] = val
                #print self._links 
            
            elif self._ContainsOnlySameChar(line):
                stripped = line.strip()
                if stripped == '..':
                    i = self._SkipCommentBlock(i)
                    continue
                elif stripped == '::':
                    i = self._HandleRawBlock(i)
                    continue
                
                prev_line = self._output_lines[-1]
                self._output_lines[-1] = 'h1. ' + prev_line
                
            else:
                stripped = line.strip()
                if stripped.startswith('..'):
                    if self._re_start_image.match(line):
                        i = self._HandleImage(i)
                        continue
                    
                    elif self._re_start_sourcecode.match(line):
                        i = self._HandleSourceCode(i)
                        continue
                    
                elif stripped.startswith(':'):
                    i = self._HandleTable(i)
                    continue
                    
                line = self._ConvertLineLinks(line)
                    
                
                self._output_lines.append(line)
        
        ret = '\n'.join(self._output_lines).replace('**', '*').replace(r'\\', '/')
        for op in self._finishing_operations:
            ret = op(ret)
        return ret


