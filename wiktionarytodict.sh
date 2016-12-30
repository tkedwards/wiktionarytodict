#!/bin/bash

#wiktionarytodict - creates dictd format dictionaries from Witkionary data
#Copyright (C) 2012 Tim Edwards

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Creates dictd format dictionaries from dump files from the English Wiktionary (http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2)

function usage {
	echo -e "usage: `basename $0` -f WIKTDUMPFILE -l \"LANGNAME1:LANGCODE1 LANGNAME2:LANGCODE2..\" [-i] [-d DICTFILESLOCATION]
LANGNAME is the language name as appears in the Wiktionary dumps eg. 'German'.
LANGCODE is the 3-letter ISO-639-3 code for the language. The output files will be named after this 3-letter codes. Run wiktionarytodict.py --showlangcodes to get a list of languages and the ISO-639-3 codes
If -i is specified the dictionaries will be installed to the local dictd server, if not they'll just be created in the path specified by DICTFILESLOCATION

Example: ./wiktionarytodict.sh ~/Downloads/enwiktionary-latest-pages-articles.xml Dutch nld install"
}

WIKTDUMPFILE=''
LANGUAGES=''
INSTALLTODICTD=0
DICTFILESLOCATION=''
while getopts "h?f:l:id:" opt; do
    case "$opt" in
    h|\?)
        usage
        exit 0
        ;;
    f)  WIKTDUMPFILE="$OPTARG"
        ;;
    l)  LANGUAGES="$OPTARG"
        ;;
    i)  INSTALLTODICTD=1
        ;;
    d)  DICTFILESLOCATION="$OPTARG"
        ;;
    :)
        usage
        exit 1
    esac
done

if [ -z "$WIKTDUMPFILE" -o -z "$LANGUAGES" ]; then # check all compulsory arguments are there
	usage
else
	if [ $INSTALLTODICTD == 1 -a ! -d "$DICTFILESLOCATION" ]; then # if the user wants the resulting files installed in the dictd location make sure it's a valid directory
		echo "ERROR: $DICTFILESLOCATION is not a valid directory"
		exit 2
	fi
	
	# generate the dictionary data and the dict format files in $ATEMPDIR
	ATEMPDIR=`mktemp -d`
	SCRIPTDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	"$SCRIPTDIR"/wiktionarytodict3.py "$WIKTDUMPFILE" $LANGUAGES "$ATEMPDIR"
	
	# either install the dictd format files directly or copy them to the specfied $DICTFILESLOCATION
	if [ $INSTALLTODICTD == 1 ]; then
		sudo cp "$ATEMPDIR"/wikt-* /usr/share/dictd/
		sudo /usr/sbin/dictdconfig --write
		sudo service dictd restart
	else
		sudo cp -f "$ATEMPDIR"/wikt-* "$DICTFILESLOCATION"
	fi
	rm -rf "$ATEMPDIR"
fi

