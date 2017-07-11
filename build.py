#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import codecs

result = os.system("python setup.py bdist_wheel")
if result != 0:
    sys.exit(result)

with codecs.open(os.path.join('LAST_VERSION'), "r", encoding='utf-8') as vf:
    ver = vf.read()

result += os.system("pip install ./dist/pythource-{ver}-py2.py3-none-any.whl".format(ver=ver))

sys.exit(result)
