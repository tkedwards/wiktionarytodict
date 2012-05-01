#!/usr/bin/env python

import codecs

def getisocodes_dict(data_path):
    # Provide a map from ISO code (both bibliographic and terminologic)
    # in ISO 639-2 to a dict with the two letter ISO 639-2 codes (alpha2)
    # English and french names
    #
    # "bibliographic" iso codes are derived from English word for the language
    # "terminologic" iso codes are derived from the pronunciation in the target 
    # language (if different to the bibliographic code)

    D = {}
    f = codecs.open(data_path, 'rb', 'utf-8')
    for line in f:
        iD = {}
        iD['bibliographic'], iD['terminologic'], iD['alpha2'], \
            iD['english'], iD['french'] = line.strip().split('|')
        D[iD['bibliographic']] = iD

        if iD['terminologic']:
            D[iD['terminologic']] = iD

        if iD['alpha2']:
            D[iD['alpha2']] = iD

        for k in iD:
            # Assign `None` when columns not available from the data
            iD[k] = iD[k] or None
    f.close()
    return D

if __name__ == '__main__':
    D = getisocodes_dict('ISO-639-2_utf-8.txt') # downloaded from http://www.loc.gov/standards/iso639-2/ascii_8bits.html
    print D['eng']
    print D['fr']

    # Print my current locale
    import locale
    print D[locale.getdefaultlocale()[0].split('_')[0].lower()]

