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
	"$SCRIPTDIR"/wiktionarytodict.sh "$1"/enwiktionary-latest-pages-articles.xml $2 $3 dontinstall "$1"
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
	
	echo "Regenerate dictionary files using wiktionary dump file in $1? (This can take a long time) DO NOT PRESS ENTER DURING DICTIONARY CREATION (y/n)"
	read
	YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		# Create dictionaries
		NUMCPUS=`grep -c ^processor /proc/cpuinfo`
		for ARGUMENT in "German deu" "Spanish spa" "Dutch nld" "Norwegian nob" "French fra"  "Italian ita" "Portuguese por" "Swedish swe" "Finnish fin" "Danish dan" "Polish pol" "Russian rus"; do
		    createdict $1 $ARGUMENT &
		    NUMPROCS=$(($NUMPROCS+1))
		    # run as many createdict processes simultaenously as there are CPUs in the machine
		    if [ "$NUMPROCS" -ge $NUMCPUS ]; then
			wait
		    NUMPROCS=0
		    fi
		done
	
		echo "Dictionaries created, replace the current ones in the packaging directory? (y/n)"
		read
        	YESORNO=$REPLY
        	if [ "$YESORNO" = "y" ]; then
			echo "Extracting the packaging directory from the most recent bundle (e.g. wiktionarytodict_20130420.tar.gz)"
			cd "$SCRIPTDIR"/packaging/ && tar -xzf wiktionarytodict_*.tar.gz
			echo "Copying dictionaries to $SCRIPTDIR/packaging/"
			cp "$1"/wikt* "$SCRIPTDIR"/packaging/wiktionarytodict
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
		echo -e "\n\nPackage creation complete. Manual steps remaining:\n- Move the .deb package files from $SCRIPTDIR/packaging/ into your apt repository\n- To save space, delete $SCRIPTDIR/packaging/wiktionarytodict (the contents of it are preserved in $SCRIPTDIR/packaging/wiktionarytodict_VERSION.tar.gz)\n- (Optional)The $SCRIPTDIR/packaging/wiktionarytodict_VERSION.tar.gz, $SCRIPTDIR/packaging/wiktionarytodict_VERSION.dsc and $SCRIPTDIR/packaging/wiktionarytodict_VERSION_ARCH.changes files can also be deleted if they're already saved in git"
	fi
fi
