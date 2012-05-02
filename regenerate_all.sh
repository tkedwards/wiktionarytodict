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

# Regenerates all dictionaries for specified languages
function createdict {
	echo "Creating dictionaries for $2"
	SCRIPTDIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	"$SCRIPTDIR"/wiktionarytodict.sh "$1"/enwiktionary-latest-pages-articles.xml $2 $3 install
}

if [ -z "$1" ]; then
       echo -e "usage: `basename $0` TEMPLOCATION
where TEMPLOCATION is the path to a directory with a few gigbytes free space"
else
	# Download and extract file (comment out if the dump file is already there)
	#cd "$1" && wget http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2 && bunzip2 enwiktionary-latest-pages-articles.xml.bz2

	# Create dictionaries
	createdict $1 German deu
	createdict $1 Spanish spa
	createdict $1 Dutch nld
	createdict $1 Norwegian nob
	
	echo "Dictionaries created, replace the current ones in setup? (y/n)"
	read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		echo "Copying dictionaries to setup/"
		cp /usr/share/dictd/wikt* /home/tim/setup/ubuntu_current/dictd_dictionaries/
	fi
	
	echo "Processing complete, do you want to delete the downloaded wiktionary dump files from $1? (y/n)"
	read
	YESORNO=$REPLY
	if [ "$YESORNO" = "y" ]; then
		rm -f "$1"/enwiktionary-latest-pages-articles.xml
	fi
fi
