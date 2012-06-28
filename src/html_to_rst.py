'''
Html to rst: Just use pandoc :)
'''

import subprocess
import sys
def html2rst(html):
    p = subprocess.Popen(['pandoc', '--from=html', '--to=rst'],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return p.communicate(html)[0]


if __name__ == '__main__':
    f = open(sys.argv[1], 'r')
    try:
        contents = f.read()
        print html2rst(contents)
    finally:
        f.close()
