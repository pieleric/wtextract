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

class wikihandler(object):
    """
    Handles one wiki page
    """
    def __init__(self, title):
        self.title = title
        self.in_nom_fr = False
        self.is_nom_fr = False
        self.gender = [] # list of strings (for each nom-fr)

    re_is_level_2 = re.compile(r"{{-\w+-(\|\w+)?}}")
    re_is_nom_fr = re.compile(r"{{-nom-\|fr}}")
    re_get_gender = re.compile(r"{{(f|m|mf)}}")
    
    def __str__(self):
        return self.title + u"\t" + u",".join(self.gender)
    
    def feed(self, data):
        m = self.re_is_level_2.search(data)
        if m:
            self.start_level_2(m.group(0))
        else:
            self.char_data(data)
        
    def start_level_2(self, name):
        """
        enters something like {{-*-|*}}
        # name should be like -nom-|fr
        """
        if self.re_is_nom_fr.match(name):
            self.in_nom_fr = True
            self.is_nom_fr = True
        else:
            # TODO: detect that no gender was given for this definition
            self.in_nom_fr = False
            
    def char_data(self, data):
        if self.in_nom_fr:
#            print data
            match = self.re_get_gender.search(data)
            if match:
                g = match.group(0).lstrip("{").rstrip("}")
                self.gender.append(g)
        

class xmlhandler(object):
    def __init__(self):
        self.in_page = False
        self.in_title = False
        self.in_content = False
        self.wh = None
        self.title = ""
        self.content = ""
        
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
            if self.wh.is_nom_fr:
                print unicode(self.wh)
            self.wh = None
            self.title = ""
            self.content = ""
        elif name == "title":
            self.wh = wikihandler(self.title)
            self.in_title = False
        elif name == "text":
            self.in_content = False
            
    def char_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_content:
            self.content += data
            self.wh.feed(data)
            
if __name__ == '__main__':     
    h = xmlhandler()
    p = xml.parsers.expat.ParserCreate()

    p.StartElementHandler = h.start_element
    p.EndElementHandler = h.end_element
    p.CharacterDataHandler = h.char_data

    f = bz2.BZ2File("/home/piel/Downloads/frwiktionary-latest-pages-articles.xml.bz2")
    p.ParseFile(f)

