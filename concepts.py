import os
import re
import weakref
from pattern.search import Taxonomy
from pattern.search import WordNetClassifier
import utilities

class Concept:
  taxonomy = Taxonomy()
  thesaurus = dict()
  
  def __init__(self, name=None, type=None, bootstrapVocabulary=False):
    if name: 
      self.name = utilities.camelCase(name)
    else: 
      self.name = None
    if type: 
      self.classify(utilities.sanitize(type))
    if bootstrapVocabulary:
      self.bootstrapVocabulary = True
      self.wordnetClassifier = WordNetClassifier()
      self.taxonomy.classifiers.append(self.wordnetClassifier)
    else:
      self.bootstrapVocabulary = False
  
  def parents(self, name=None):
    if not name:
      names = self.synonyms()
    else:
      names = self.synonyms(name)
    response = set()
    for name in names:
      name = utilities.sanitize(name)
      if name.istitle():
        self.taxonomy.classifiers = []
        self.taxonomy.case_sensitive = True
      if not getattr(self, 'isVerb', False):
        response |= set(utilities.unicodeDecode(self.taxonomy.parents(name, recursive=False)))
      else:
        response |= set(utilities.unicodeDecode(self.taxonomy.parents(name, recursive=False, pos='VB')))
      if name.istitle():
        if self.bootstrapVocabulary:
          self.taxonomy.classifiers.append(self.wordnetClassifier)
        self.taxonomy.case_sensitive = False
    return response
    
  def ancestors(self, name=None):
    if not name: 
      names = self.synonyms()
    else:
      names = self.synonyms(name)
    response = set()
    for name in names:
      name = utilities.sanitize(name)
      if name.istitle():
        self.taxonomy.classifiers = []
        self.taxonomy.case_sensitive = True
      if not getattr(self, 'isVerb', False):
        response |= set(utilities.unicodeDecode(self.taxonomy.parents(name, recursive=True)))
      else:
        response |= set(utilities.unicodeDecode(self.taxonomy.parents(name, recursive=True, pos='VB')))
      if name.istitle():
        if self.bootstrapVocabulary:
          self.taxonomy.classifiers.append(self.wordnetClassifier)
        self.taxonomy.case_sensitive = False
        temp = set()
        for term in response:
          if not utilities.sanitize(term).istitle():
            temp |= set(utilities.unicodeDecode(self.taxonomy.parents(utilities.sanitize(term), recursive=True)))
        response |= temp
    return response
    
  def descendants(self, name=None):
    if not name: 
      names = self.synonyms()
    else:
      names = self.synonyms(name)
    response = set()
    for name in names:
      name = utilities.sanitize(name)
      if name.istitle(): return
      if not getattr(self, 'isVerb', False):
        firstPass = utilities.unicodeDecode(self.taxonomy.children(name, recursive=False))
      else:
        firstPass = utilities.unicodeDecode(self.taxonomy.children(name, recursive=False, pos='VB'))
      for thing in firstPass:
        if utilities.sanitize(thing).istitle():
          continue
        else:
          response |= set(utilities.unicodeDecode(self.descendants(thing)))
      response |= set(firstPass)
    return response
    
  def classify(self, term1, term2=None):
    if re.match('^!', term1):
      return False
    if term2:
      if re.match('^!', term2):
        return False
    if not term2:
      if not self.isVerb:
        if not utilities.sanitize(term1).istitle():
          self.classify(term1, utilities.sanitize(term1).split()[-1])
      child = self.name
      parent = term1
    else:
      child = term1
      parent = term2
    if child == parent: return
    child = utilities.sanitize(child)
    parent = utilities.sanitize(parent)
    if not self.isA(child, parent) and not parent.istitle():
      self.taxonomy.case_sensitive = True
      self.taxonomy.append(child, type=parent)
      self.taxonomy.case_sensitive = False
    
  def isA(self, term1, term2=None):
    if not term2:
      if not self.name:
        return False
      childTerms = self.synonyms()
      parent = term1
    else:
      childTerms = self.synonyms(term1)
      parent = term2
    existingParents = set()
    for child in childTerms:
      child = utilities.sanitize(child)
      parent = utilities.sanitize(parent)
      if child == parent: return True
      if child.istitle() or parent.istitle():
        self.taxonomy.classifiers = []
        self.taxonomy.case_sensitive = True
      if not getattr(self, 'isVerb', False):
        existingParents |= set(map(str, self.taxonomy.parents(child, recursive=True)))
      else:
        existingParents |= set(map(str, self.taxonomy.parents(child, recursive=True, pos='VB')))
      if child.istitle() or parent.istitle():
        if self.bootstrapVocabulary:
          self.taxonomy.classifiers.append(self.wordnetClassifier)
        self.taxonomy.case_sensitive = False
        temp = set()
        for term in existingParents:
          if not utilities.sanitize(term).istitle():
            temp |= set(map(str, self.taxonomy.parents(utilities.sanitize(term), recursive=True)))
        existingParents |= temp
    for term in self.synonyms(parent):
      if utilities.sanitize(term) in existingParents:
        return True
    return False

  def equate(self, *phrases):
    if self.name: 
      if not re.match('^unspecified', self.name):
        phrases += (self.name,)
    phrases = map(utilities.camelCase, phrases)
    phraseSets = map(self.synonyms, phrases)
    mergedSet = set.union(*phraseSets)
    for phrase in mergedSet:
      self.thesaurus[phrase] = mergedSet
      
  def synonyms(self, phrase=None):
    if not phrase:
      if not self.name:
        return None
      else:
        phrase = self.name
    phrase = utilities.camelCase(phrase)
    listOfSetsWithPhrase = []
    for key in self.thesaurus:
      if phrase in self.thesaurus[key]:
        if self.thesaurus[key] not in listOfSetsWithPhrase:
          listOfSetsWithPhrase.append(self.thesaurus[key])
    if len(listOfSetsWithPhrase) == 0:
      self.thesaurus[phrase] = {phrase}
    elif len(listOfSetsWithPhrase) > 1:
      mergedSet = set.union(*listOfSetsWithPhrase)
      for element in mergedSet:
        self.thesaurus[element] = mergedSet
    elif phrase not in self.thesaurus:
      self.thesaurus[phrase] = listOfSetsWithPhrase[0]
    return self.thesaurus[phrase]
    

  

		