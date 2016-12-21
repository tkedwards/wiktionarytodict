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
	echo -e "usage: `basename $0` WIKTDUMPFILE LANGNAME LANGCODE install/dontinstall [DICTFILESLOCATION]
LANGNAME is the language name as appears in the Wiktionary dumps eg. 'German'.
LANGCODE is the 3-letter ISO-639-3 code for the language. The output files will be named after this 3-letter codes. Run wiktionarytodict.py --showlangcodes to get a list of languages and the ISO-639-3 codes
install/dontinstall controls whether to install the dictionaries to the local dictd server or just create them in the path specified by DICTFILESLOCATION

Example: ./wiktionarytodict.sh ~/Downloads/enwiktionary-latest-pages-articles.xml Dutch nld install"
}

if [ -z "$1" -o -z "$2" -o -z "$3" -o -z "$4" ]; then
	usage
else
	if [ "$4" == "dontinstall" -a -d "$5" ]; then
		# DICTFILESLOCATION is a valid directory
		DICTFILESLOCATION="$5"
	elif [ "$4" == "dontinstall" -a ! -d "$5" ]; then
		echo "ERROR: $5 is not a valid directory"
		exit 2
	fi
	ATEMPDIR=`mktemp -d`
	SCRIPTDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	"$SCRIPTDIR"/wiktionarytodict3.py $1 $2 $3 "$ATEMPDIR"
	echo "Creating dictd format dictionaries in $ATEMPDIR"
	dictfmt --utf8 --allchars -s "Wiktionary English to $2" -j "$ATEMPDIR"/wikt-eng-$3 < "$ATEMPDIR"/eng-$3.txt
	dictfmt --utf8 --allchars -s "Wiktionary $2 to English" -j "$ATEMPDIR"/wikt-$3-eng < "$ATEMPDIR"/$3-eng.txt
	dictzip "$ATEMPDIR"/*.dict # compress the plain-text dictionaries into 'dictzip' format
	if [ "$4" == "install" ]; then
		sudo cp "$ATEMPDIR"/wikt-* /usr/share/dictd/
		sudo /usr/sbin/dictdconfig --write
		sudo service dictd restart
	else
		sudo cp -f "$ATEMPDIR"/wikt-* "$DICTFILESLOCATION"
	fi
	rm -rf "$ATEMPDIR"
fi

