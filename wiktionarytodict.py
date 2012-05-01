#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys, codecs, re, pycountry

class WiktionaryDumpHandler(ContentHandler):
	def __init__ (self, language, langcode, outputdir):
		self.isTitleElement = 0
		self.isTextElement = 0
		self.word = u''
		self.isEnglishWord = 0
		self.translationsfromeng = {}
		self.translationstoeng = {}
		# the language to create a dictionary to
		self.language = language
		self.langcode = langcode # ISO 639-3 language code, e.g. 'deu' for German 
		self.textchardata = ''
		self.outputdir = outputdir

	def processTextElement(self, content):
		# The content of each Wiktionary page is contained in the <text> elemnt.
		# This script is only interested in the ====Translations==== section for words marked ==English==
		#ucontent = unicode(content, "utf-8")
		for aline in content.splitlines():
			if '==English==' in aline:
				self.isEnglishWord = 1
				self.parseTranslations(content)

	def parseTranslations(self, content):
		inTransSection = 0
		currentMeaning = ''
		for aline in content.splitlines():
			transbegin = re.compile("\{\{trans-top")
			transend = re.compile("\{\{trans-bottom")
			if transbegin.match(aline) != None:
				inTransSection = 1
				splitresult = aline.split('|')
				if len(splitresult) < 2:
					# handle the case where there's no refinement on the meaning (just a '{{trans-top}}')
					currentMeaning = ''
				else:
					currentMeaning = splitresult[1].strip('{}')
			elif transend.match(aline) != None:
				inTransSection = 0
				currentMeaning = ''
			else: # not a {{trans-top or {{trans-bottom line
				if inTransSection == 1:
					self.parseTranslationline(aline, currentMeaning)

	def parseTranslationline(self, aline, currentMeaning):
		if self.pickLanguageLines(aline) == 1:
			wordwithmeaning = self.word + ' (%s)' % (currentMeaning) # word with meaning, e.g. "trade (practice)": Handwerk
			# TODO: deal with these qualifiers properly
			aline = re.sub('\{\{qualifier\|[\w ]*\}\}', '', aline) # remove qualifier crap (eg. {{qualifier|man}}) from strings like this: * German: {{qualifier|man}} [[Scheißkerl]] {{m}}, [[Drecksack]] {{m}}
			if aline.startswith('*:'): # sub-language lines like '*: Bokmål:'
				rawtranslation = aline.split(':')[2].lstrip()
			else: # normal language lines like '* Norwegian:'
				rawtranslation = aline.split(':')[1].lstrip()
			if rawtranslation.startswith('{{'): # lines formatted like this: {{t+|de|frei}}
				translationslist = rawtranslation.split('{{')
				for atranslation in translationslist:
					bits = atranslation.strip('} ,').split('|')
					if len(bits) > 2:
						translation = bits[2] # the actual word
						if len(bits) > 3:
							translation += ' (%s)' % bits [3] # noun gender if specified
						self.addtoTranslationsMap(wordwithmeaning, translation)
					else:
						pass # TODO: log to stderr here printing the atranslation
			elif rawtranslation.startswith('[['): # lines formatted like this: [[gratis#German|gratis]], [[kostenlos]], [[frei]], [[kostenfrei]]
				translationslist = rawtranslation.split(',')
				for atranslation in translationslist:
					bits = atranslation.strip('][ ,').split('|')
					if len(bits) > 1:
						translation = bits[1] # e.g. from "[[gratis#German|gratis]]" pick out "gratis"
					elif len(bits) == 1:
						translation = bits[0]
					else:
						pass # TODO: log to stderr here printing the atranslation
					self.addtoTranslationsMap(wordwithmeaning, translation)
			else: # lines formatted like this: Der [[groß|Große]] [[Teich]]
				wordlist = rawtranslation.split('[[')
				translation = ''
				for aword in wordlist:
					bits = aword.split('|')
					if len(bits) > 1:
						translation += bits[1] # e.g. 'Große' from '[[groß|Große]'
					else:
						translation += bits[0]
				self.addtoTranslationsMap(wordwithmeaning, translation)
	def addtoTranslationsMap(self, wordwithmeaning, translation):
		if self.translationsfromeng.has_key(wordwithmeaning):
			# add multiple translations together, eg: free (make free) : freisetzen, befreien
			newtrans = self.translationsfromeng[wordwithmeaning] + ', %s' % translation
			self.translationsfromeng[wordwithmeaning] = newtrans
		else:
			self.translationsfromeng[wordwithmeaning] = translation
		
		if self.translationstoeng.has_key(translation):
			newtrans = self.translationstoeng[translation] + ', %s' % wordwithmeaning
                        self.translationstoeng[translation] = newtrans
		else:
			self.translationstoeng[translation] = wordwithmeaning
			
	def pickLanguageLines(self, aline):
		# only return true if aline is really for the current language
		langNameFormat1 = '%s:' % self.language # e.g. German:
		langNameFormat2 = '%s]]' % self.language # e.g. German]]
		if self.language == 'Norwegian':
			# (TODO fix)special case for Norwegian due to its 2 spelling systems.
			# By default uses Bokmål, replace 'Bokmål' with 'Nynorsk' in the line below to use that
			if u'*: Bokmål' in aline:
				return 1
		if (langNameFormat1 in aline) or (langNameFormat2 in aline):
			if('{{trreq' not in aline): # filter out translation requests (http://en.wiktionary.org/wiki/Template:trreq/doc)
				return 1
		return 0
		
	def outputJargonFormat(self):
		# output to Jargon File format (see the -j option in man dictfmt)
		fromeng = open(('%s/eng-%s.txt' % (self.outputdir, self.langcode)).encode('utf-8'), 'w')
		fromengheader = "This dictionary tranlsates English to %s. It was created by the script %s and is based on data from the Wiktionary dumps available from http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2\nAll content in this dictionary is under the same license as Wiktionary content.\n\n" % (self.language, sys.argv[0])
		fromeng.write(fromengheader.encode('utf-8'))
		for akey in self.translationsfromeng.keys():
			# split out the headword, e.g. dictionary, from the explanation
			#print ("DEBUG akey is %s" % akey).encode('utf-8')
			if akey.find('(') != -1:
				(headword, explanation) = akey.split('(', 1)
				headword = headword.rstrip()
				explanation = explanation[:-1] # remove last char (an extra ')')
				explanation = '(%s) ' % explanation
			else:
				headword = akey
				explanation = ''
			#print ("DEBUG about to write %s" % headword).encode('utf-8')
			fromeng.write((':%s:%s%s\n' % (headword, explanation, self.translationsfromeng[akey])).encode('utf-8'))
		fromeng.close()

		toeng = open(('%s/%s-eng.txt' % (self.outputdir, self.langcode)).encode('utf-8'), 'w')
		toengheader = "This dictionary tranlsates %s to English. It was created by the script %s and is based on data from the Wiktionary dumps available from http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2\nAll content in this dictionary is under the same license as Wiktionary content.\n\n" % (self.language, sys.argv[0])
		toeng.write(toengheader.encode('utf-8'))
		for akey in self.translationstoeng.keys():
			if akey.find('(') != -1:
				(headword, explanation) = akey.split('(', 1)
				headword = headword.rstrip()
                                explanation = explanation[:-1] # remove last char (an extra ')')
                                explanation = '(%s) ' % explanation
			elif akey.find('{') != -1:
                                (headword, explanation) = akey.split('{', 1)
				headword = headword.rstrip()
                                explanation = explanation[:-1] # remove last char (an extra ')')
                                explanation = '(%s) ' % explanation
			else:
				headword = akey
				explanation = ''
			toeng.write((':%s:%s%s\n' % (headword, explanation, self.translationstoeng[akey])).encode('utf-8'))
		toeng.close()

	def startElement(self, name, attrs):
		if name=='title':
			self.isTitleElement=1
		if name=='text':
                        self.isTextElement=1

	def characters (self, content):
		if self.isTitleElement==1:
			# the page title should be the headword, but filter out Wiktionary crap
			if 'Wiktionary:' not in content:
				self.word = content
		if self.isTextElement==1:
			self.textchardata += content
	
	def ignorableWhitespace (self, whitespace):
		self.word = u''

	def endElement(self, name):
		#if self.isEnglishWord==1:
		#	print self.word.encode('utf-8')
		if self.isTitleElement == 1:
			self.isTitleElement = 0
		if self.isTextElement == 1:
			self.processTextElement(self.textchardata)
			self.textchardata = ''
			self.isTextElement = 0
			self.isEnglishWord = 0
			self.word = ''

def usage():
	print "usage: %s FILE LANGUAGE OUTPUTDIR" % sys.argv[0]
	print "%s --showlangcodes" % sys.argv[0]

if (len(sys.argv) > 4):
	parser = make_parser()
	curHandler = WiktionaryDumpHandler(sys.argv[2], sys.argv[3], sys.argv[4])
	parser.setContentHandler(curHandler)
	parser.parse(open(sys.argv[1], 'r'))
	curHandler.outputJargonFormat()
elif (len(sys.argv) == 2):
	if sys.argv[1] == '--showlangcodes':
		langlist = []
		for lang in list(pycountry.languages):
			  langlist.append(lang)
		for lang in sorted(langlist):
			print ("%s:%s" % (lang.name, pycountry.languages.get(name=lang.name).terminology)).encode("utf-8")
	else:
		usage()
else:
	usage()
