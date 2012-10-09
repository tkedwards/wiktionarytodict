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

# Get the directory this script is being called from
SCRIPTDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Regenerates all dictionaries for specified languages
function createdict {
	echo "Creating dictionaries for $2"
	"$SCRIPTDIR"/wiktionarytodict.sh "$1"/enwiktionary-latest-pages-articles.xml $2 $3 install
}

if [ -z "$1" ]; then
       echo -e "usage: `basename $0` TEMPLOCATION
where TEMPLOCATION is the path to a directory with a few gigbytes free space"
else
	echo "Download the latest Wiktionary dump file and extract it? (y/n)"
        read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		cd "$1" && wget http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2 && bunzip2 -f enwiktionary-latest-pages-articles.xml.bz2
	fi
	
	echo "Regenerate dictionary files using wiktionary dump file in $1? (This can take a long time) (y/n)"
	read
	YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		# Create dictionaries
		createdict $1 German deu
		createdict $1 Spanish spa
		createdict $1 Dutch nld
		createdict $1 Norwegian nob
		createdict $1 French fra
	
		echo "Dictionaries created, replace the current ones in the packaging directory? (y/n)"
		read
        	YESORNO=$REPLY
        	if [ "$YESORNO" = "y" ]; then
			echo "Copying dictionaries to $SCRIPTDIR/packaging/"
			cp /usr/share/dictd/wikt* "$SCRIPTDIR"/packaging/wiktionarytodict
		fi
	fi

	echo "Do you want to delete the downloaded wiktionary dump files from $1? (y/n)"
        read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
                rm -f "$1"/enwiktionary-latest-pages-articles.xml
        fi

	echo "Regenerate the Debian Package? (y/n)"
	read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		cd "$SCRIPTDIR"/packaging/wiktionarytodict
		echo "Enter the new version of the package (e.g. 20120630): "
		read
		NEWVER=$REPLY
		dch --newversion "$NEWVER"
		dpkg-buildpackage -rfakeroot
		echo -e "\n\nPackage creation complete. You should now move the .deb package files from $SCRIPTDIR/packaging/ into your apt repository."
	fi
fi
