import os
import re


version_pattern = r"[0-9]+\.[0-9]+\.[0-9]$"

version = input('请输入版本号: ')

if not re.match(version_pattern, version):
    raise SystemExit('版本号不合法')

os.system('git tag %s' % version)
os.system('python setup.py bdist_wheel')

os.system('git add .')
os.system('git commit -m "release [%s]"' % version)
os.system('git push')
