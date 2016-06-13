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
	WORKINGDIR="`mktemp -d --tmpdir="$1" wiktionarytodict_build.XXX`"
	echo "Download the latest Wiktionary dump file and extract it? (y/n)"
        read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		cd "$WORKINGDIR" && wget http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2 && bunzip2 -f enwiktionary-latest-pages-articles.xml.bz2
	fi
	
	echo "Regenerate dictionary files using wiktionary dump file in $WORKINGDIR? (This can take a long time) DO NOT PRESS ENTER DURING DICTIONARY CREATION (y/n)"
	read
	YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
		# Create dictionaries
		NUMCPUS=`grep -c ^processor /proc/cpuinfo`
		for ARGUMENT in "German deu" "Spanish spa" "Dutch nld" "Norwegian nob" "French fra"  "Italian ita" "Portuguese por" "Swedish swe" "Finnish fin" "Danish dan" "Polish pol" "Russian rus"; do
		    createdict $WORKINGDIR $ARGUMENT &
		    NUMPROCS=$(($NUMPROCS+1))
		    # run as many createdict processes simultaenously as there are CPUs in the machine
		    if [ "$NUMPROCS" -ge $NUMCPUS ]; then
			wait
		    NUMPROCS=0
		    fi
		done
		# Bundle up the dictionaries in a .tar.gz file (effectively a new 'release' that's ready to be packaged for Debian or other distros)
		echo "Dictionaries created. Enter the new release version for wiktionarytodict (e.g. 20120630, NOT 20120630-1): "
		read
		NEWVER=$REPLY
		NEW_RELEASE_TAR="wiktionarytodict_$NEWVER.orig.tar.gz" # e.g. wiktionarytodict_20160710.tar.gz
		NEW_RELEASE_DIR="wiktionarytodict-$NEWVER" # e.g. wiktionarytodict-20160710
		cd "$WORKINGDIR" && mkdir -p "$NEW_RELEASE_DIR"
                cp wikt* "$NEW_RELEASE_DIR"
                tar -czf "$NEW_RELEASE_TAR" "$NEW_RELEASE_DIR"/
                cp "$NEW_RELEASE_TAR" "$SCRIPTDIR"/packaging/
	fi

	echo "Do you want to delete the downloaded wiktionary dump files from $WORKINGDIR? (y/n)"
        read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
                rm -f "$WORKINGDIR"/enwiktionary-latest-pages-articles.xml
        fi

	echo "Regenerate the Debian Package? (y/n)"
        read
        YESORNO=$REPLY
        if [ "$YESORNO" = "y" ]; then
                ## Prepare the packaging directories
                echo "Extracting the packaging directory from the most recent Debian source package (e.g. wiktionarytodict_20160110.dsc)"
                cd "$SCRIPTDIR"/packaging/
                CURRENT_DSC_FILE="`ls -1 wiktionarytodict_*.dsc | sort | tail -1`"
                CURRENT_RELEASE_DIR=`echo "${CURRENT_DSC_FILE%-*}" | tr _ -` #e.g. wiktionarytodict-20160110 
                cd "$SCRIPTDIR"/packaging/ && dpkg-source -x $CURRENT_DSC_FILE # extract the most recent existing source package, e.g. wiktionarytodict_20160110-1.dsc
                NEW_RELEASE_TAR="`ls -1 wiktionarytodict_*.orig.tar.gz | sort | tail -1`" # get the name of the most recent wiktionarytodict_*.orig.tar.gz file in packaging/, this should've been copied in at the end of the regenerate dictionaries procedure above
                tar -xf "$NEW_RELEASE_TAR" # extract out original source
                NEW_RELEASE_DIR="`find . -maxdepth 1 -type d | sort | tail -1`" # find the directory created by the above 'tar -xf' command
                cp -r "$CURRENT_RELEASE_DIR"/debian "$NEW_RELEASE_DIR" # copy over the debian/ directory to the new release's directory
    
                ## Create the new package
		cd "$SCRIPTDIR"/packaging/"$NEW_RELEASE_DIR"
		echo "Enter the new release version for package (suggested: $NEWVER-1): "
		read
		NEWPKGVER=$REPLY
		dch --newversion "$NEWPKGVER"
                debuild -S # Source only build, needed for source.changes file to use for Launchpad upload. Run just 'debuild' to build binary packages
		debuild clean
		cat "$SCRIPTDIR"/regenerate_all_manualsteps.txt
	fi
fi
