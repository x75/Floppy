#!python3

import sys
import glob
# import subprocess

from subprocess import Popen, PIPE



if __name__ == '__main__':
    wd = sys.argv[-1]
    report = []
    for file in glob.glob(wd):
        # x = subprocess.call(, shell=True)
        p = Popen(['python.exe', 'Floppy.py', '--test', '{}'.format(file)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate(b"input data that is passed to subprocess' stdin")
        rc = p.returncode
        r = eval(err.decode())
        report.append((file, r))
        # for line in err.readlines():
        #     print(line)
    print('Test Result:')
    for f, r in report:
        print('   {1:6} -- {0} {2}'.format(f, 'Passed' if not r[0] else 'Failed', r[1] if r[0] else ''))

