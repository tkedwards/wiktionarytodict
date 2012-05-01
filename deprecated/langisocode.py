#!/usr/bin/env python

import pycountry, sys

print (pycountry.languages.get(name=sys.argv[1]).terminology).encode('utf-8')
