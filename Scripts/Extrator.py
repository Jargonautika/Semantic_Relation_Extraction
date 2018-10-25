#!/usr/bin/env python

import os
import glob
import spacy
import Shortest_Dependency_Path

from collections import Counter
from lxml import etree as ET

nlp = spacy.load('en')


def merge(sentList):
    # Returns a dictionary with a single key and a list of annotations,
    # all of which fall in that key's sentence for a given passageText
    # Looks like - {0: [<Element annotation at 0x2266de46948>, <Element annotation at 0x2266de46608>]}
    d = dict()
    d[list(sentList[0].keys())[0]] = [list(sent.values())[0] for sent in sentList]
    return d


def sentSplitter(passageText):
    # This function returns a list of dictionaries.
    # Each individual dictionary represents a sentence in the passageText
    # The dictionary is of the form {sentence Number (0-indexed) : (tuple where
    # x is the start index and y is the end index)}
    # e.g. [{0:(0,27)}, {1:(28,56)}]

    doc = nlp(passageText)
    sentList = list()
    sentCount = -1
    # Sentence tokenization step. How many sentences are in a given passageText?
    for sent in doc.sents:
        sentCount += 1
        # x is the sentence index. passageText could be an entire abstract, so we have to know which
        # sentence we are dealing with inside of that larger paragraph or paragraphs
        x = str(doc).index(str(sent))
        # y gives the character offsets for a given sentence
        y = x + len(str(sent))
        sentList.append({sentCount:(x,y)})
    return sentList


def coOccurrence(passage):
    coOccurrenceList = list()
    sentList = list()
    # Each infon in a passage contains some bit of metadata related to the title or abstract that it is
    # Some of these deal with offset/length information. Others are actually 'annotations'
    # The 'text' infon tag here refers to the actual string that is the title or abstract
    checkTypeList = list()
    for infon in passage:
        if infon.tag == 'text':
        # Get the offsets for the sentence here. It is not yet clear whether these are actually 100% correct or
        # if the 2015 PubTator known error with off-by(x) issues is still extant in this version.
        # Regardless, the sentList represents how many sentences are in a given passageText
            sentList = sentSplitter(infon.text)

        # The annotation infon contains the named entity that has been encoded.
        elif infon.tag == 'annotation':
            # sent is a dictionary with sentence indices as key and offset tuples as value
            for sent in sentList:
                sentNum = list(sent.keys())[0]
                for location in infon:
                    if location.tag == 'location':
                        sentOff = list(sent.values())[0][0]
                        sentLen = list(sent.values())[0][1]
                        annoOff = int(location.attrib.values()[0])
                        annoLen = int(location.attrib.values()[1])

                        p = infon.find('location').attrib.values()
                    
                        # Corroborate that for a given annotation, it is indeed found within a single sentence.
                        # The second half indicates that it is not a duplicate of itself that has been tagged with
                        # a different annotation type.
                        if annoOff >= sentOff and annoOff + annoLen <= sentLen and p not in checkTypeList:
                            coOccurrenceList.append({sentNum:infon})
                            checkTypeList.append(p)
    #print(checkTypeList)
    if coOccurrenceList == []:
        return None
    else:
        #print(coOccurrenceList)
        # Return a list containing lists with all of the annotations grouped together by sentence they fall into.
        corroborationMasterList = [(passage.find('infon').text,(passage.find('offset'),passage.find('text')))]
        sentNumList = list()
        # coOccurrenceList contains a number of dictionaries that have a key representing which sentence they fall into
        # and a value which is the annotation that falls into that sentence.
        # Here we want to put all of those annotations together so that we can compare them.
        for d in coOccurrenceList:
            sentNumList.append(list(d.keys())[0])
            
        if len([item for item, count in Counter(sentNumList).items() if count > 1]) > 0:
            overlapList = [item for item, count in Counter(sentNumList).items() if count > 1]
            for x in overlapList:
                sendList = list()
                for d in coOccurrenceList:
                    if list(d.keys())[0] == x:
                        sendList.append(d)
                # sendList represents a list of dictionaries which values all fall within a given natural language sentence
                corroborationList = merge(sendList)
                corroborationMasterList.append(corroborationList)
        if len(corroborationMasterList) > 1:
            return corroborationMasterList

for file in glob.glob('../Data/Extracted/*ioC.xml'):
    # Reads in the large files from PubTator that were downloaded over FTP dated early 2017.
    # These files are too large to be read into memory and thus we use the iterparse
    # method to slowly go through them document by document. Each one represents roughly a million documents
    print(os.path.basename(file))
    counter = 0

    for event, document in ET.iterparse(file, tag='document'):

        counter += 1
        if counter > 200:
            break

        PMID = None
        
        if document.tag == 'document':
            # Retrieve the unique identifying information for the PubMed ID of the document
            masterList = [document.find('id').text]
            for passage in document:
                if passage.tag == 'id':
                    PMID = passage.text
                    # These passages represent the titles and abstracts of a given PubMed article
                    # In PubMed Central (PMC), in PubMed Central articles these will also represent
                    # deeper structure such as sections and subsections of an article.
                elif passage.tag == 'passage':
                    corroborationMasterList = coOccurrence(passage)
                    if corroborationMasterList != None and corroborationMasterList != []:
                        masterList.append(corroborationMasterList)
                passage.clear()
            if len(masterList) > 1:
                Shortest_Dependency_Path.myFunct(masterList)
                # Clear the node after dealing with it so as to not lose out on memory
                document.clear()
            else:
                # For nodes which are iteratively parsed but which are not tagged as documents
                document.clear()

        document.clear()

        print(counter)
