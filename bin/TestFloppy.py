#!python3

import sys
import glob
# import subprocess

from subprocess import Popen, PIPE, TimeoutExpired



if __name__ == '__main__':
    wd = sys.argv[-1]
    report = []
    for file in glob.glob(wd):
        if 'Lauescript' in file:
            continue
        p = Popen(['python.exe', 'Floppy.py', '--test', '{}'.format(file)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        # print(['python.exe', 'Floppy.py', '--test', '{}'.format(file)])
        try:
            output, err = p.communicate("", timeout=20)
        except TimeoutExpired:
            report.append((file, (1, 'Unkown Error')))
        else:
            rc = p.returncode
            r = eval(err.decode())
            report.append((file, r))
        # for line in err.readlines():
        #     print(line)
    print('Test Result:')
    for f, r in report:
        print('   {1:6} -- {0:50} {2}'.format(f, 'Passed' if not r[0] else 'Failed', r[1] if r[0] else ''))

