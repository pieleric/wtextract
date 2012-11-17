#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.parsers.expat
import bz2
import re

"""
In fr wiktionary, the french words are described using {{-nom-|fr}} (until the next {{-*-}}).
If masculin: {{m}} {{msing}}
if feminin: {{f}} {{fsing}}
if both: {{mf}} 
It can have several entries, both might be any of the forms.
TODO: Maybe also save plural form? (note if {{invar}} {{invariable}} {{*sing}}?)
every word starting with vowel or h have l' instead of le/la, excepted if h is "aspiré"
({{h|*}}). Also not clear for Y: it seems it has elision if it's pronounced like 'i' (and
not 'j'), which is about the same as there is a consonant afterwards.
+ a few like onze/onzieme/11e, héro 


Test:
eau
maire
livre
in-trente-deux
hotel
avocat
onze
fille
chose
"""

# according to many grammar books, there is no appostrophe is h aspiré or these
# "2" words. However, it's not sure all h aspiré words are classified, and there
# might be more exceptions, so need to check!
no_apostrophe = [u"onze", u"onzième", u"héro", u"11", u"11e", u"i", u"y"]

class wikihandler(object):
    """
    Handles one wiki page
    """
    def __init__(self, title):
        self.title = title
        self.in_nom_fr = False
        self.is_nom_fr = False
        self.gender = [] # list of strings (for each nom-fr)
        # e if normally elided
        # i if starts with y that sounds like i (=> elided)
        # h if h aspiré
        # n if could find an example of the word without elision
        # y if could find an example with the elision
        # N if part of whitelist not in elision
        self.elision = set() # set of strings
        
        # manage elision
        if self.re_has_elision.match(title.lower()):
            self.elision.add("e")
        if title in no_apostrophe:
            self.elision.add("N")
        

    re_is_level_2 = re.compile(r"{{-\w+-(\|\w+)?}}")
    re_is_nom_fr = re.compile(r"{{-(nom|lettre)-\|fr}}")
    
    re_has_elision = re.compile(u"(a|â|à|ä|e|é|è|ê|ë|i|ì|ï|o|ò|ô|ö|u|ù|û|ü|h).*") # the basic rule 
    re_is_h_aspire = re.compile(u"{{h( aspiré)?(\\|[^}]*)*}}")
    re_pron_starts_with_i = re.compile(r"{{pron\|i.*}}")
    # some words definitions don't have gender explicitly but have a table
    # For example Juif {{fr-accord-if|Ju|ʒɥ}} => m
    re_get_gender = re.compile(r"{{(f|fsing|m|msing|mf)(\|[^}]*)*}}")
    gender_2_letter = {"f": "f", "fsing": "f", "m": "m", "msing": "m", "mf": "mf"}
    
    def __str__(self):
        return u"%s\t%s\t%s" % (self.title, u",".join(self.gender), u",".join(sorted(self.elision)))
    
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
            # don't match special pages
            if self.title.startswith("Wiktionnaire:"):
                return
            self.in_nom_fr = True
            self.is_nom_fr = True
            # TODO {{-flex-nom-|fr}}, e.g. Juive
            
            # TODO cet + mon/ton/son on feminine words are also sign of elision
            # tricky because of false positives in coloquial examples: "Y’a pas l’feu."
            safet = re.escape(self.title)
            # cet hiver/l'hiver/d'hiver
            self.re_example_elision = re.compile(u"\\b(cet\\s|(l|d)('|’))(''')?%s\\b" % safet) # ''' is for bold formatting
            self.re_example_no_elision = re.compile(u"\\b(la|le|du|de|ce|ma|ta|sa)\\s(''')?%s\\b" % safet)
            
        else:
            # TODO: detect that no gender was given for this definition
            self.in_nom_fr = False
            
            
    def char_data(self, data):
        if self.in_nom_fr:
#            print data
            match = self.re_get_gender.search(data)
            if match:
                g = self.gender_2_letter[match.group(1)]
                self.gender.append(g)
            # search elision
            if self.re_is_h_aspire.search(data):
                self.elision.add("h")
            if self.title.lower()[0] == "y" and self.re_pron_starts_with_i.search(data):
                self.elision.add("i")
            if self.re_example_elision.search(data):
                self.elision.add("y")
            if self.re_example_no_elision.search(data):
                self.elision.add("n")
                
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
                print unicode(self.wh).encode("utf-8")
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

