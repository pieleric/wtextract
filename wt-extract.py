#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.parsers.expat
import bz2
import re

"""
In fr wiktionary, the french words are described using {{-nom-|fr}} (until the next {{-*-}}).
If masculin: {{m}} 
if feminin: {{f}}
if both: {{mf}} 
It can have several entries, both might be any of the forms.
TODO: Maybe also save plural form? (noter si {{invar}}?)
every word starting with vowel or h have l' instead of le/la.


Test:
eau
maire
livre
in-trente-deux
hotel
avocat
"""


class xmlhandler(object):
    def __init__(self):
        self.in_page = False
        self.in_title = False
        self.in_content = False
        self.title = ""
        self.content = ""
        self.re_is_nom_fr = re.compile(r"{{-nom-\|fr}}")
        
    # 3 handler functions
    def start_element(self, name, attrs):
#        print 'Start element:', name, attrs
        if name == "page":
            self.in_page = True
        elif name == "title" and self.in_page:
            self.in_title = True
        elif name == "text" and self.in_page:
            self.in_content = True
            
    def end_element(self, name):
#        print 'End element:', name
        if name == "page":
            self.in_page = False
            if self.re_is_nom_fr.search(self.content):
                print "%s" % self.title.encode('utf-8')
#                print "%s:\n%s" % (self.title, self.content)
            self.title = ""
            self.content = ""
        elif name == "title":
            self.in_title = False
        elif name == "text":
            self.in_content = False
            
    def char_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_content:
            self.content += data
    
        
     
h = xmlhandler()
p = xml.parsers.expat.ParserCreate()

p.StartElementHandler = h.start_element
p.EndElementHandler = h.end_element
p.CharacterDataHandler = h.char_data

f = bz2.BZ2File("/home/piel/Downloads/frwiktionary-latest-pages-articles.xml.bz2")
p.ParseFile(f)

