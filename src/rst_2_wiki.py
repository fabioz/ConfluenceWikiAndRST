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
        self._re_inline_emphasis = re.compile(r'\*([^ ]+[^*]*[^ ])\*')
        self._re_inline_strong = re.compile(r'\*\*([^ ]+[^*]*[^ ])\*\*')
        self._re_inline_literal = re.compile(r'``([^`]*)``')
        self._re_inline_link = re.compile(r'`([^ ]+[^`]*[^ ]+) <([^> ]*)>`_')
        self._re_link_definition = re.compile(r'(\s)*\.\.(\s)*_(`)?((\w|\s|:|/|\.)*)(`)?:(.*)')
        self._re_link_definition1 = re.compile(r'(\s)*\.\.(\s)*_(`)((\w|\s|:|/|\.)*)(`):(.*)')
        self._re_link_use = re.compile(r'`((\w|\s|:|/|\.)*)`_')
        # Note: Directive types are followed by two colons with no blanks
        # e.g.:    .. directive_type:: directive
        # Ref: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#directives
        self._re_start_image = re.compile(r'\s*\.\.(\s)*(image|figure)(\s)*\:\:(\s)*(.*)')
        self._re_start_sourcecode = re.compile(r'\s*\.\.(\s)*(code|sourcecode)(\s)*\:\:(\s)*(.*)')
        self._re_start_admonition = re.compile(r'\s*\.\.(\s)*(attention|caution|danger|error|hint|important|note|tip|warning)(\s)*\:\:(\s)*(.*)')
        self._re_start_attention = re.compile(r'\s*\.\.(\s)*attention(\s)*\:\:(\s)*(.*)')
        self._re_start_caution = re.compile(r'\s*\.\.(\s)*caution(\s)*\:\:(\s)*(.*)')
        self._re_start_danger = re.compile(r'\s*\.\.(\s)*danger(\s)*\:\:(\s)*(.*)')
        self._re_start_error = re.compile(r'\s*\.\.(\s)*error(\s)*\:\:(\s)*(.*)')
        self._re_start_hint = re.compile(r'\s*\.\.(\s)*hint(\s)*\:\:(\s)*(.*)')
        self._re_start_important = re.compile(r'\s*\.\.(\s)*important(\s)*\:\:(\s)*(.*)')
        self._re_start_note = re.compile(r'\s*\.\.(\s)*note(\s)*\:\:(\s)*(.*)')
        self._re_start_tip = re.compile(r'\s*\.\.(\s)*tip(\s)*\:\:(\s)*(.*)')
        self._re_start_warning = re.compile(r'\s*\.\.(\s)*warning(\s)*\:\:(\s)*(.*)')
        self._re_start_sphinx_index = re.compile(r'\s*\.\.(\s)*index(\s)*\:\:(\s)*(.*)')
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
        
        # WORKAROUND: drop spaces between directive type and the two colons
        dir_line = self._lines[start]
        bad_dir_match = re.search("(\s)+\:\:", dir_line)
        if bad_dir_match is not None:
            dir_line = "%s::%s" % (dir_line[:bad_dir_match.start()],
                                   dir_line[bad_dir_match.end():])
        # END WORAROUND
        match = self._re_start_image.match(dir_line)
        # In the normalized line, 'match.group(5)' points to the image file
        url = self._images_prefix + match.group(5).strip()
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

    def _HandleSphinxIndex(self, i):
        #start = i
        end = self._SkipCommentBlock(i)
        # Confluence treats headings as anchors and provides anchors creation,
        # with the {anchor:name} macro, but does not provide a way to define
        # index entries
        # TODO: Removing leads to loss of semantic
        return end

    def _HandleAdmonition(self, i):
        start = i
        end = self._SkipCommentBlock(i)

        dir_line = self._lines[start]
        # Identify admonition type
        if (self._re_start_attention.match(dir_line)):
            # No "attention" in Confluence, change to "warning"
            admonition_type = "warning"
        elif self._re_start_caution.match(dir_line):
            # No "caution" in Confluence, change to "warning"
            admonition_type = "warning"
        elif self._re_start_danger.match(dir_line):
            # No "danger" in Confluence, change to "warning"
            admonition_type = "warning"
        elif self._re_start_error.match(dir_line):
            # No "error" in Confluence, change to "warning"
            admonition_type = "warning"
        elif self._re_start_hint.match(dir_line):
            # No "hint" in Confluence, change to "info"
            admonition_type = "info"
        elif self._re_start_important.match(dir_line):
            # No "important" in Confluence, change to "info"
            admonition_type = "info"
        elif self._re_start_note.match(dir_line):
            admonition_type = "note"
        elif self._re_start_tip.match(dir_line):
            admonition_type = "tip"
        elif self._re_start_warning.match(dir_line):
            admonition_type = "warning"

        # WORKAROUND: drop spaces between directive type and the two colons
        bad_dir_match = re.search("(\s)+\:\:", dir_line)
        if bad_dir_match is not None:
            dir_line = "%s::%s" % (dir_line[:bad_dir_match.start()],
                                   dir_line[bad_dir_match.end():])
        # END WORAROUND

        match = self._re_start_admonition.match(dir_line)
        try:
            # Attempt to get the actual admonition title, if defined
            # In the normalized line, 'match.group(5)' points to the title
            admonition_title = match.group(5).strip()
        except IndexError:
            # Default admonition title
            admonition_title = admonition_type.capitalize()
        line = '{%s:title=%s}\n' % (admonition_type, admonition_title)
        for i in xrange(start + 1, end + 1):
            line += '\n' + self._lines[i]
        line += '\n{%s}' % admonition_type

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
    
    
    def _ConvertInlineLiterals(self, line):
        # Inline literal, from ``literal`` to {{literal}}
        literal_marker_len = len('``')  # 2, using len() to clarify only
        match = self._re_inline_literal.search(line)
        while match is not None:
            line = "%s{{%s}}%s" % (line[:match.start()],
                                   line[(match.start() + literal_marker_len):
                                        (match.end() - literal_marker_len)],
                                   line[match.end():])
            match = self._re_inline_literal.search(line, match.end())
        return line

    def _ConvertInlineStrongAndEmphasis(self, line):
        # Inline strong, from **strong** to *strong*
        # Inline emphasis, from *emphasis* to _emphasis_
        # An intermediate transformation is required
        # 1) **strong** to intermediate
        strong_marker_len = len('**')  # 2, using len() to clarify only
        match = self._re_inline_strong.search(line)
        while match is not None:
            line = "%s(TMP_STRONG_MARKER)%s(TMP_STRONG_MARKER)%s" % \
                            (line[:match.start()],
                             line[(match.start() + strong_marker_len):
                                  (match.end() - strong_marker_len)],
                             line[match.end():])
            match = self._re_inline_strong.search(line, match.end())
        # 2) *emphasis* to _emphasis_
        emphasis_marker_len = len('*')  # 1, using len() to clarify only
        match = self._re_inline_emphasis.search(line)
        while match is not None:
            line = "%s_%s_%s" % \
                            (line[:match.start()],
                             line[(match.start() + emphasis_marker_len):
                                  (match.end() - emphasis_marker_len)],
                             line[match.end():])
            match = self._re_inline_emphasis.search(line, match.end())
        # 1) intermediate to *strong*
        line = line.replace('(TMP_STRONG_MARKER)', '*')
        return line

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

    def _ConvertInlineLinks(self, line):
        match = self._re_inline_link.search(line)
        inline_link_start_mark_len = len('`')
        inline_link_end_mark_len = len('>`_')
        while match is not None:
            line = "%s[%s|%s]%s" % \
                            (line[:match.start()],
                             match.group(1),
                             match.group(2),
                             line[match.end():])
            match = self._re_inline_link.search(line, match.end())
        return line
    

    
    
    def _DoInitialReplacements(self):
        '''
        Replace 'foo' by the associated tag value
        '''
        re_definition = re.compile(r'(\s)*\.\.(\s)*\|((\w|\s|:|/|\.)+)\|(.*)')
        replacements = {}
        i = -1
        while i < self._line_count - 1:
            i += 1
            line = self._lines[i]
            stripped = line.strip()
            if stripped.startswith('..'):
                if stripped[2:].strip().startswith('|'):
                    match = re_definition.match(stripped)
                    if match:
                        replacements['|%s|' % match.group(3).strip()] = '.. '+ match.group(5).strip()
                        self._lines[i] = ''
        
        
        i = -1
        while i < self._line_count - 1:
            i += 1
            line = self._lines[i]
            for key, val in replacements.iteritems():
                line = line.replace(key, val)
            self._lines[i] = line
                    
        
    
    def Convert(self):
        self._DoInitialReplacements()
        self._output_lines = []
        
        i = -1
        while i < self._line_count - 1:
            i += 1
            line = self._lines[i]
            
            if line.strip() == '.. contents::':
                self._output_lines.append('{toc:style=circle|minLevel=1|maxLevel=5}')
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
                    
                    # Additional handlers
                    elif self._re_start_admonition.match(line):
                        i = self._HandleAdmonition(i)
                        continue
                    
                    elif self._re_start_sphinx_index.match(line):
                        i = self._HandleSphinxIndex(i)
                        continue
                    
                elif stripped.startswith(':'):
                    i = self._HandleTable(i)
                    continue
                    
                line = self._ConvertInlineLiterals(line)
                line = self._ConvertInlineStrongAndEmphasis(line)
                line = self._ConvertLineLinks(line)
                line = self._ConvertInlineLinks(line)
                    
                
                self._output_lines.append(line)
        
        ret = '\n'.join(self._output_lines).replace(r'\\', '/')
        for op in self._finishing_operations:
            ret = op(ret)
        return ret


