#!/usr/bin/env python

import csv
import spacy
import itertools
import numpy as np
import networkx as nx
from lxml import etree as ET
from itertools import chain, combinations

nlp = spacy.load('en')


def lex2Dep(deps, y):

    intList = [int(item.split('-')[-1]) for item in y]
    returnList = [deps[i] for i in intList]

    return returnList

# This function may be better served as a recursive function which sends all powersets up to the lex2Dep
# function above. This would allow for all groups of two to be added together and then the tuples,
# thruples, and quadruples could be correlated with those concatenated dependency paths.
# The trick will be to send the appropriate levels to different outputs. We need all tuples in a
# dataframe and all thruples and quadruples separated for analysis.
# Also maintain ordinality based off of the token.i functionality.


def powerSet(s):

    return chain.from_iterable(combinations(s,r) for r in range(len(s)+1))
    

def shortestDepPath(deps, graph, newEntityList, typeList):

    if len(newEntityList) > 1:
        print('newEntityList looks like', newEntityList)
        pS = list(powerSet(newEntityList))
        print('pS looks like ', pS)

        resultSet = list()
        for result in pS:
            if len(result) > 1:
               print(result) 
               resultSet.append(result)
        
        return ()
    
    # Needs more help with getting multiples over 2 in a newEntityList
    # Needs to take n entities in newEntityList as an input
    # Need to make sure that they are distinct entities (PubTator Annotation Type needs to factor in)
    # Need to concatenate a list when there are three+ distinct entities represented
    # Need to keep the order of precedence (smallest to largest)
    """
    n = len(newEntityList)
    listOfLists = list()
    
    for result in powerSet(newEntityList):
        if len(result) == 2 and result[0] != result[1]:
            j = [result[0].split('-')[0], result[1].split('-')[0]]
            try:
                y = nx.shortest_path(graph, source=result[0], target=result[1])
                formattedList = lex2Dep(deps, y)
                for tup in list(zip(newEntityList, typeList)):
                    if result[0] in tup[0] and formattedList[0] != tup[1]:
                        formattedList[0] = tup[1]
                    elif result[1] in tup[0] and formattedList[-1] != tup[1]:
                        formattedList.append(tup[1])
                if (j, formattedList) not in listOfLists:
                    listOfLists.append((j,formattedList))

            except:
                # Sometimes the sentTokenizer of spaCy doesn't work as expected and it will return two (or more?) sentences.
                # That means that all of the entities in newEntityList that end up in this function, shortestDepPath,
                # may not actually have a path between them. This except routes those out and returns nothing to downstream. 
                pass
        else:
            print(result)
    if listOfLists != None and listOfLists != []:

        return listOfLists
    """

# passageText is the lxml Element which contains the passageText. Get it by using passageText.text
# entityList here is the same as the myPowerSet list below in makeGraph
# annoOffnText here is a tuple of the form (passageOffsetAnno, passageTextAnno)
def reformat(annoOffnText, entityList):

    for anno in entityList:
        annoText = anno[0].find('text').text
        annoLoc = anno[0].find('location').attrib
        
        if ' ' in annoText or '-' in annoText:

            anno[0].find('text').text = annoText.replace(' ', '_').replace('-', '_')
            
            firstBit = annoOffnText[1].text[:(int(annoLoc.values()[0])-int(annoOffnText[0].text))]
            newBit = annoOffnText[1].text[(int(annoLoc.values()[0]) - int(annoOffnText[0].text)) : (int(annoLoc.values()[0]) + int(annoLoc.values()[1]) - int(annoOffnText[0].text))].replace(' ', '_').replace('-', '_')
            if newBit != anno[0].find('text').text:
                newBit = annoOffnText[1].text[int(annoLoc.values()[0]) : (int(annoLoc.values()[0]) + int(annoLoc.values()[1]))].replace(' ', '_').replace('-', '_')
                if newBit != anno[0].find('text').text:
                    raise Exception
            lastBit = annoOffnText[1].text[(int(annoLoc.values()[0]) - int(annoOffnText[0].text) + int(annoLoc.values()[1])):]

            annoOffnText[1].text = firstBit + newBit + lastBit

    return annoOffnText, entityList

        
# A note about myPowerSet:
# This variable is a list that contains 2+ tuples which each have an annotation
# and a blank spot. The format looks like this:
# [(annotation,), (annotation,), ... ]

def makeGraph(annoOffnText, myPowerSet):

    # newPassageText is an lxml Element with an updated .text
    # newEntityList has reformatted entities (spaces taken out so far)
    # newEntityList also comes in the format [(entityAddress,),(entityObject,)]
    newAnnoOffnText, newEntityList = reformat(annoOffnText, myPowerSet)

    edges, deps, heads = list(), list(), list()
    doc = nlp(newAnnoOffnText[1].text)

    realNewEntityList = list()
    duplicateChecker = list()
    typeList = list()
    for token in doc:
        deps.append(token.dep_)
        heads.append(token.head)

        for annotation in newEntityList:
            if (int(annotation[0].find('location').attrib.values()[0]) - int(newAnnoOffnText[0].text)) == token.idx and int(annotation[0].find('location').attrib.values()[1]) == len(token.text) and annotation not in duplicateChecker:
                realNewEntityList.append(annotation[0].find('text').text + '-' + str(token.i))
                duplicateChecker.append(annotation)
                annoType = None
                for infon in annotation[0]:
                    if infon.tag == 'infon' and infon.attrib.values()[0] == 'type':
                        annoType = infon.text.strip()
                typeList.append(annoType)
                
        for child in token.children:
            edges.append(('{0}-{1}'.format(token,token.i),
                          '{0}-{1}'.format(child,child.i)))

    assert len(realNewEntityList) == len(duplicateChecker), "It appears that you don't have as many annotations in duplicateChecker as you do entities in realNewEntityList."
    assert len(realNewEntityList) == len(typeList), "It appears that you don't have as many types in typeList as you do entities in realNewEntityList."
    graph = nx.Graph(edges)
    
    x = shortestDepPath(deps, graph, realNewEntityList, typeList)
    print(list(zip(heads, deps)))
    print(x)
    
    if x != None:
        for item in x:
            c = csv.writer(open('../Data/dataFrames/{0}_{1}.csv'.format(item[1][0], item[1][-1]), 'a'))
            c.writerow([item[0], item[1]])

            p = csv.writer(open('../Data/dataFrames/withSentences/{0}_{1}_sent.csv'.format(item[1][0], item[1][-1]), 'a'))
            p.writerow([item[0], item[1], doc.text])
                  
    
# The masterList comes in a very specific format that looks like the following:
# ['PMID', [('passageType', (passageOffsetAnno, passageTextAnno)), {int(sentNum): [annotation, annotation, ... ]}]]
def myFunct(masterList):
    annoList = list(masterList[1][1].values())[0]
    for i in range(0,len(annoList)+1):
        # Is this actually a powerSet?
        myPowerSet = list(itertools.combinations(annoList, i))
        if len(myPowerSet) > 1:
            makeGraph(masterList[1][0][1], myPowerSet)
