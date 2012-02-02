import xmlrpclib

  

s = xmlrpclib.ServerProxy('https://wiki.appcelerator.org/rpc/xmlrpc')

user, password = raw_input('user pass').split()
auth = s.confluence1.login(user, password)
print auth
for p in s.confluence1.getPages(auth, 'tis'):
    page = str(p).lower()
    if 'python' in page or 'pydev' in page:
        print 'Getting page: ', p['title']
        print s.confluence1.getPage(auth, 'tis', p['title'])
s.confluence1.logout(auth)

#issue = s.jira1.getIssue(auth, 'PROJ-28')