import xmlrpclib
import os
import httplib

class TimeoutHTTPConnection(httplib.HTTPSConnection):
    def connect(self):
        httplib.HTTPSConnection.connect(self)
        self.sock.settimeout(self.timeout)

class TimeoutHTTP(httplib.HTTPS):
    _connection_class = TimeoutHTTPConnection
    def set_timeout(self, timeout):
        self._conn.timeout = timeout

class TimeoutTransport(xmlrpclib.Transport):
    def __init__(self, timeout=30, *l, **kw):
        xmlrpclib.Transport.__init__(self, *l, **kw)
        self.timeout = timeout
    def make_connection(self, host):
        conn = TimeoutHTTP(host)
        conn.set_timeout(self.timeout)
        return conn

class TimeoutServerProxy(xmlrpclib.ServerProxy):
    def __init__(self, uri, timeout=30, *l, **kw):
        kw['transport'] = TimeoutTransport(timeout=timeout, use_datetime=kw.get('use_datetime', 0))
        xmlrpclib.ServerProxy.__init__(self, uri, *l, **kw)



#=======================================================================================================================
# Executer
#=======================================================================================================================
class Executer(object):


    def Login(self):
        if not hasattr(self, 'server_proxy'):
            self.server_proxy = TimeoutServerProxy('https://wiki.appcelerator.org/rpc/xmlrpc')

            user, password = raw_input('user pass').split()
            self.auth = self.server_proxy.confluence1.login(user, password)


    def Logout(self):
        if hasattr(self, 'server_proxy'):
            self.server_proxy.confluence1.logout(self.auth)
            del self.server_proxy


    def _LoadAndConvertPage(self, space, p, title):
        print 'Getting page: ', title
        page = self.server_proxy.confluence1.getPage(self.auth, space, p['title'])

        content = page['content']
        url = page['url']
        filename = os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents', p['title'] + '.wiki')
        if os.path.exists(filename):
            f = file(filename, 'r')
            try:
                current_contents = f.read()
            finally:
                f.close
            if current_contents == content:
                print 'Content still the same.'
                return #No need to gather html because it's the same!


        f = file(filename, 'w')
        try:
            f.write(content)
        finally:
            f.close()

        print 'Obtaining html content...'
        page_html = self.server_proxy.confluence1.renderContent(self.auth, space, p['id'], page['content'])
        f = file(os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents', p['title'] + '.html'), 'w')
        try:
            f.write(page_html)
        finally:
            f.close()

    def LoadPages(self, space):
        self.Login()
        for p in self.server_proxy.confluence1.getPages(self.auth, space):
            title = str(p['title']).lower()
            if 'python' in title or 'pydev' in title:
                for i in xrange(3):
                    try:
                        self._LoadAndConvertPage(space, p, title)
                        break
                    except:
                        import traceback;traceback.print_exc()
                        print 'Retrying...'


    def PrintSpaces(self):
        self.Login()
        print self.server_proxy.confluence1.getSpaces(self.auth)


    def ConvertCodeToHtml(self, code):
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters import get_formatter_by_name
        lexer = get_lexer_by_name('python')
        formatter = get_formatter_by_name('html', noclasses=True)
        return highlight(code, lexer, formatter)


    def _ConvertInCode(self, title, contents, start, end, convert_code_to_html):
        i_start = contents.find(start)
        found = 0
        while i_start >= 0:
            i_end = contents.find(end, i_start + len(start))
            if i_end >= 0:
                found += 1
                converted = convert_code_to_html(contents[i_start + len(start):i_end])
                contents = list(contents)
                contents[i_start:i_end + len(end)] = converted
                contents = ''.join(contents)
                i_start = contents.find(start)
            else:
                break

        #Just a quick check as we know that this page has some code, to make sure that we got it.
        if 'Django' in title:
            assert found > 0, 'Found: %s' % (found,)
        return contents


    def ConvertToPyDev(self):
        base = r'x:/pydev/plugins/com.python.pydev.docs/'

        import sys
        sys.path.append(r'x:/pydev/plugins/com.python.pydev.docs/merged_homepage/scripts')
        import build_merged #@UnresolvedImport

        manual_adv = build_merged.manualAdv
        manual_101 = build_merged.manual101
        homepage_base = build_merged.homepageBase
        manual_screencasts = build_merged.manualScreencasts

        all = manual_101 + manual_adv + homepage_base + manual_screencasts


        wiki_contents = os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents')
        wiki_html_files = set()
        for f in os.listdir(wiki_contents):
            if f.endswith('.html'):
                wiki_html_files.add(f)

        #Remove files in wiki but not in the homepage
        wiki_html_files.discard('Python Development.html') #index is different.

        title_to_filename = {}
        urls_replacement = {}
        for template, filename, title in all:
            title_to_filename[title] = filename
            title = title.lower()
            if not title.startswith('pydev'):
                title = 'pydev+' + title
            urls_replacement[('"/display/tis/' + (title.replace(' ', '+')) + '"')] = '"' + filename + '.html"'

        import re
        link_re = re.compile(r'\"/display/tis/(.)*?\"')
        for template, filename, title in all:
            #Skip the pages that are in the homepage but not in the wiki
            skip = title in (
                'Manual', #Grouper, always from actual homepage.
                'PyDev', #index differs
                'About', #about only in homepage
                'PyDev Releases', #History only in main homepage
                'PyDev Extensions Releases', #History only in main homepage
                'Screenshots',
                'Screencasts',
                'Screencast: Starring: Interactive Console',
                )

            html_name = 'PyDev ' + title + '.html'


            wiki_html_files.discard(html_name)
            path_wiki_html = os.path.join(wiki_contents, html_name)
            if os.path.exists(path_wiki_html):
                if skip:
                    raise AssertionError('Expected that %s would be skipped and it was not.' % (title,))
            else:
                if skip:
                    continue
                print >> sys.stderr, 'SKIPPED', path_wiki_html

            path_html_rst = os.path.join(r'x:\pydev\plugins\com.python.pydev.docs\merged_homepage', title_to_filename[title] + '.rst')
            if os.path.exists(path_html_rst):
                os.remove(path_html_rst)

            path_html_rst = os.path.join(r'x:\pydev\plugins\com.python.pydev.docs\merged_homepage', title_to_filename[title] + '.contents.rst')
            if os.path.exists(path_html_rst):
                os.remove(path_html_rst)

            path_html = os.path.join(r'x:\pydev\plugins\com.python.pydev.docs\merged_homepage', filename + '.contents.html')
            print path_wiki_html, '\t\t->>\t\t', path_html
            f = open(path_wiki_html, 'r')
            try:
                contents = f.read()
            finally:
                f.close()

            assert contents.count('<body>') == 1
            assert contents.count('</body>') == 1
            start = contents.find('<body>')
            end = contents.find('</body>')
            contents = contents[start:end]

            page_link = title
            if not page_link.lower().startswith('pydev'):
                page_link = 'PyDev+' + page_link
            page_link = page_link.replace(' ', '+')

            contents += '<br/><br/><a href="https://wiki.appcelerator.org/display/tis/%s">See wiki page</a>\n</body>' % (page_link,)

            #Fix html links in contents
            #i.e.: change /display/tis/PyDev+Running+a+program to manual_101_run.html
            #Fix: "/display/tis/PyDev+Module+Creation"
            match = link_re.search(contents)
            while match is not None:
                group = match.group(0).lower()
                start = match.start(0)
                end = match.end(0)
                contents = list(contents)
                try:
                    replacement = urls_replacement[group]
                except:
                    if group == '"/display/tis/changing+the+update+type"':
                        replacement = 'https://wiki.appcelerator.org/display/tis/Changing+the+Update+Type'
                    else:
                        print 'Available:\n' + ('\n'.join(sorted(urls_replacement.iterkeys())))
                        raise
                contents[start:end] = replacement
                contents = ''.join(contents)
                match = link_re.search(contents)


            #Now, deal with code-samples
            contents = self._ConvertInCode(
                title,
                contents,
                '<script type="syntaxhighlighter" class="theme: Default; brush: python; gutter: false"><![CDATA[',
                ']]></script>',
                self.ConvertCodeToHtml
            )




            contents = contents.replace('<body>', '<contents_area>').replace('</body>', '</contents_area>')
            contents = '<doc>\n' + contents + '\n</doc>'
            f = open(path_html, 'w')
            try:
                f.write(contents)
            finally:
                f.close()




        if wiki_html_files:
            error_msg = 'Found in wiki but not in html: %s' % (wiki_html_files,)
            raise AssertionError(error_msg)

        print 'Finished converting to the PyDev homepage format.'





#    def ConvertPages(self):
#        path = os.path.join(r'W:\ConfluenceWikiAndRST', 'wiki_contents')
#        for filename in os.listdir(path):
#            if filename.endswith('.wiki'):
#                f = file(os.path.join(path, filename), 'r')
#                try:
#                    contents = f.read()
#                    self.server_proxy.confluence1.renderContent(self.auth, space)
#                finally:
#                    f.close()

if __name__ == '__main__':

    loader = Executer()
    #loader.PrintSpaces()
    loader.LoadPages('tis')
#    loader.ConvertPages()
    loader.ConvertToPyDev()
    loader.Logout()
    #issue = self.server_proxy.jira1.getIssue(self.auth, 'PROJ-28')


