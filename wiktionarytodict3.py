#!/usr/bin/env python3

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
import sys, codecs, re, pycountry, time, subprocess

class WiktionaryDumpHandler(ContentHandler):
    def __init__ (self, languages, langcodes, outputdir):
        self.isTitleElement = 0
        self.isTextElement = 0
        self.word = ''
        self.isEnglishWord = 0
        self.translationsfromeng = {}
        self.translationstoeng = {}
        # the languages to create a dictionary to
        self.languages = languages
        self.textchardata = ''
        self.outputdir = outputdir
        # intialise the data structures
        for langname in list(self.languages.keys()):
            self.translationsfromeng[langname] = {}
            self.translationstoeng[langname] = {}

    def processTextElement(self, content):
        # The content of each Wiktionary page is contained in the <text> elemnt.
        # This script is only interested in the ====Translations==== section for words marked ==English==
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

    def parseTranslationline(self, currentLine, currentMeaning):
        (currentLanguage, bLanguageMatched) = self.pickLanguageLines(currentLine)
        if bLanguageMatched == 1:
            wordwithmeaning = self.word + ' ({0})'.format(currentMeaning) # word with meaning, e.g. "trade (practice)": Handwerk
            # TODO: deal with these qualifiers properly
            currentLine = re.sub('\{\{qualifier\|[\w ]*\}\}', '', currentLine) # remove qualifier crap (eg. {{qualifier|man}}) from strings like this: * German: {{qualifier|man}} [[Scheißkerl]] {{m}}, [[Drecksack]] {{m}}
            # Extract the actual translation (the bit we're interested in e.g. '{{t+|de|Stuhl|m}}') from the line e.g. '* German: {{t+|de|Stuhl|m}}', also works for sub-languages e.g. '*: Bokmål: {{t+|nb|stol|m}}'
            regex = re.compile("^.*\:(.*)$")
            rawtranslation = regex.findall(currentLine)[0].lstrip()
            # Process the actual translation:
            if rawtranslation.startswith('{{'): # lines formatted like this: {{t+|de|frei}}
                translationslist = rawtranslation.split('{{')
                for atranslation in translationslist:
                    bits = atranslation.strip('} ,').split('|')
                    if len(bits) > 2:
                        translation = bits[2] # the actual word
                        if len(bits) > 3:
                            translation += ' ({0})'.format(bits[3]) # noun gender if specified
                        self.addtoTranslationsMap(wordwithmeaning, translation, currentLanguage)
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
                    self.addtoTranslationsMap(wordwithmeaning, translation, currentLanguage)
            else: # lines formatted like this: Der [[groß|Große]] [[Teich]]
                wordlist = rawtranslation.split('[[')
                translation = ''
                for aword in wordlist:
                    bits = aword.split('|')
                    if len(bits) > 1:
                        translation += bits[1] # e.g. 'Große' from '[[groß|Große]'
                    else:
                        translation += bits[0]
                self.addtoTranslationsMap(wordwithmeaning, translation, currentLanguage)

    def addtoTranslationsMap(self, wordwithmeaning, translation, currentLanguage):
        if wordwithmeaning in self.translationsfromeng[currentLanguage]:
            # add multiple translations together, eg: free (make free) : freisetzen, befreien
            newtrans = self.translationsfromeng[currentLanguage][wordwithmeaning] + ', {0}'.format(translation)
            self.translationsfromeng[currentLanguage][wordwithmeaning] = newtrans
        else:
            # it's a word we haven't translated yet for this language
            self.translationsfromeng[currentLanguage][wordwithmeaning] = translation
        
        if translation in self.translationstoeng:
              # if the word's already in there make sure we add multiple translations together
              newtrans = self.translationstoeng[currentLanguage][translation] + ', {0}'.format(wordwithmeaning)
              self.translationstoeng[currentLanguage][translation] = newtrans
        else:
            # it's a word we haven't translated yet for this language
            self.translationstoeng[currentLanguage][translation] = wordwithmeaning
            
    def pickLanguageLines(self, currentLine):
        languageOfCurrentLine = ''
        if('{{trreq' in currentLine):
            return (languageOfCurrentLine, 0) # filter out translation requests (http://en.wiktionary.org/wiki/Template:trreq/doc)
        matchesFormat1 = re.findall('^\*\s(\w+):', currentLine) # test if the line begins with a language name of this form: * Lithuanian:
        matchesFormat2 = re.findall('^\*\s\[\[(\w+)\]\]:', currentLine) # test if the line begins with a language name of this form: * [[Luxembourgish]]:
        matchesFormat3 = re.findall('^\*:\s(\w+):', currentLine) # test if the line beings with a sub-language/dialect name of the form: *: Bokmål:
        if matchesFormat1:
            languageOfCurrentLine = matchesFormat1[0]
        elif matchesFormat2:
            languageOfCurrentLine = matchesFormat2[0]
        elif matchesFormat3:
            languageOfCurrentLine = matchesFormat3[0]
        else:
            return (languageOfCurrentLine, 0) # not a translation line
        
        if languageOfCurrentLine in list(self.languages.keys()):
            return (languageOfCurrentLine, 1)
        elif languageOfCurrentLine == 'Bokmål' and 'Norwegian' in list(self.languages.keys()):
            # (TODO fix)special case for Norwegian due to its 2 spelling systems.
            # By default uses Bokmål, replace 'Bokmål' with 'Nynorsk' in the line above to use that
            return ('Norwegian', 1)
        else:
            return (languageOfCurrentLine, 0) # the language of the current translation line is not one of the languages we're looking for
        
    def outputJargonFromEngFile(self, language):
        # output to Jargon File format (see the -j option in man dictfmt)
        # even in Python 3 we need to .encode('utf-8') strings before writing to a file as file.write accepts only byte data (see http://pythoncentral.io/encoding-and-decoding-strings-in-python-3-x/)
        fromeng = open(('{0}/eng-{1}.txt'.format(self.outputdir, self.languages[language])), 'wb')
        fromengheader = "This dictionary tranlsates English to {0}. It was created by the script {1} and is based on data from the Wiktionary dumps available from http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2\nAll content in this dictionary is under the same license as Wiktionary content.\n\n".format(language, sys.argv[0])
        fromeng.write(fromengheader.encode('utf-8'))
        for akey in list(self.translationsfromeng[language].keys()):
            # split out the headword, e.g. dictionary, from the explanation
            #print ("DEBUG akey is %s" % akey).encode('utf-8')
            if akey.find('(') != -1:
                (headword, explanation) = akey.split('(', 1)
                headword = headword.rstrip()
                explanation = explanation[:-1] # remove last char (an extra ')')
                explanation = '({0}) '.format(explanation)
            else:
                headword = akey
                explanation = ''
            #print ("DEBUG about to write %s" % headword).encode('utf-8')
            fromeng.write((':{0}:{1}{2}\n'.format(headword, explanation, self.translationsfromeng[language][akey])).encode('utf-8'))
        fromeng.close()
        
    def outputJargonToEngFile(self, language):
        # output to Jargon File format (see the -j option in man dictfmt)
        # even in Python 3 we need to .encode('utf-8') strings before writing to a file as file.write accepts only byte data (see http://pythoncentral.io/encoding-and-decoding-strings-in-python-3-x/)
        toeng = open(('{0}/{1}-eng.txt'.format(self.outputdir, self.languages[language])).encode('utf-8'), 'wb')
        toengheader = "This dictionary tranlsates {0} to English. It was created by the script {1} and is based on data from the Wiktionary dumps available from http://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2\nAll content in this dictionary is under the same license as Wiktionary content.\n\n".format(language, sys.argv[0])
        toeng.write(toengheader.encode('utf-8'))
        for akey in list(self.translationstoeng[language].keys()):
            if akey.find('(') != -1:
                 (headword, explanation) = akey.split('(', 1)
                 headword = headword.rstrip()
                 explanation = explanation[:-1] # remove last char (an extra ')')
                 explanation = '({0}) '.format(explanation)
            elif akey.find('{') != -1:
                 (headword, explanation) = akey.split('{', 1)
                 headword = headword.rstrip()
                 explanation = explanation[:-1] # remove last char (an extra ')')
                 explanation = '({0}) '.format(explanation)
            else:
                 headword = akey
                 explanation = ''
            toeng.write((':{0}:{1}{2}\n'.format(headword, explanation, self.translationstoeng[language][akey])).encode('utf-8'))
        toeng.close()
        
    def outputJargonFormat(self):
        for language in list(self.languages.keys()):
            print("Creating 'jargon' format file (see the -j option in man dictfmt) for {0} in {1}".format(language, self.outputdir))
            self.outputJargonFromEngFile(language)
            self.outputJargonToEngFile(language)
            
    def createDictdFormatFiles(self):
        # runs external commands to convert the files created by outputJargonFormat into dict format (see man dictfmt)
        for language in list(self.languages.keys()):
            langcode = self.languages[language]
            print("Creating dict format file (see man dictfmt) for {0} in {1}".format(language, self.outputdir))
            subprocess.run("dictfmt --utf8 --allchars -s \"Wiktionary English to {0}\" -j {1}/wikt-eng-{2} < {1}/eng-{2}.txt".format(language, self.outputdir, langcode), shell=True, check=True)
            subprocess.run("dictfmt --utf8 --allchars -s \"Wiktionary {0} to English\" -j {1}/wikt-{2}-eng < {1}/{2}-eng.txt".format(language, self.outputdir, langcode), shell=True, check=True)
        subprocess.run("dictzip {0}/*.dict".format(self.outputdir), shell=True, check=True) # compress the plain-text dictionaries into 'dictzip' format
            

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
        self.word = ''

    def endElement(self, name):
        if self.isTitleElement == 1:
            self.isTitleElement = 0
        if self.isTextElement == 1:
            self.processTextElement(self.textchardata)
            self.textchardata = ''
            self.isTextElement = 0
            self.isEnglishWord = 0
            self.word = ''

def usage():
    print("usage: {0} FILE LANGUAGE_NAME1:LANGUAGE_CODE1 LANGUAGE_NAME2:LANGUAGE_CODE2... OUTPUTDIR".format(sys.argv[0]))
    print("{0} --showlangcodes".format(sys.argv[0]))
    print("example: {0} enwiktionary-test-data-spanish.xml Spanish:spa German:deu ~/Downloads/tempdir".format(sys.argv[0]))

if (len(sys.argv) > 4):
    # get the list of languages and language codes that the user specified
    languages = {}
    for language in sys.argv[2:-1]:
        name,code = language.split(':')
        languages[name] = code # ISO 639-3 language code, e.g. 'deu' for German 
    parser = make_parser()
    curHandler = WiktionaryDumpHandler(languages, sorted(languages.keys()), sys.argv[-1])
    parser.setContentHandler(curHandler)
    parser.parse(open(sys.argv[1], 'r'))
    print("Dictionary generation complete")
    curHandler.outputJargonFormat()
    curHandler.createDictdFormatFiles()
elif (len(sys.argv) == 2):
    if sys.argv[1] == '--showlangcodes':
       for lang in list(pycountry.languages):
           print("{0}:{1}".format(lang.name, lang.terminology))
    else:
        usage()
else:
    usage()
