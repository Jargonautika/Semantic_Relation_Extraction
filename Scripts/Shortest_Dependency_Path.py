#!/usr/bin/env python

import csv
import spacy
import itertools
import numpy as np
import networkx as nx
from lxml import etree as ET
from itertools import chain, combinations

nlp = spacy.load('en')


def depMerge(y, deps):
    returnList = list()

    for i, item in enumerate(y):
        returnList.append(item)
        for dep in deps:
            first = int(y[i].split('-')[-1])
            second = None
            try:
                second = int(y[i+1].split('-')[-1])
            except:
                pass

            if first == dep[1] and second != None and second == dep[2]:
                returnList.append(dep[0])
            elif first == dep[2] and second != None and second == dep[1]:
                returnList.append(dep[0])
    return returnList


# This function may be better served as a recursive function which sends all powersets up to the lex2Dep
# function above. This would allow for all groups of two to be added together and then the tuples,
# thruples, and quadruples could be correlated with those concatenated dependency paths.
# The trick will be to send the appropriate levels to different outputs. We need all tuples in a
# dataframe and all thruples and quadruples separated for analysis.
# Also maintain ordinality based off of the token.i functionality.


def powerSet(s):
    # Returns a chain object (which can be turned into a list)
    # The length of the chain will be 2^len(s)
    return chain.from_iterable(combinations(s,r) for r in range(len(s)+1))
    

def shortestDepPath(deps, graph, newEntityList, typeList, annoOffnText):

    if len(newEntityList) > 1:
        pS = list(powerSet(newEntityList))
        #print('pS looks like ', pS)
        tL = list(powerSet(typeList))

        zL = list(zip(pS, tL))
        
        resultSet = list()
        for result in zL:
            if len(result[0]) > 1:
                resultSet.append(result)
        #print(resultSet)

        returnList = list()
        # results come in tuple format of an indeterminate length. At a minimum
        # they are 2 elements long. The max is unforeseeable, so iterate through them
        for result in resultSet:
            # i is the index within the resultSet tuple/n-uple
            resultList = list()
            for i in range(len(result)-1):
                #print(result, i)
                try:
                    y = nx.shortest_path(graph, source=result[i][0], target=result[i][1])
                except:
                    continue
                if len(y) > 2:

                    y = depMerge(y, deps)

                    for term in y:
                        if term in result[0]:
                            r = result[0].index(term)
                            resultList.append(result[1][r])
                        else:
                            resultList.append(term.split('-')[0])

            u = (k.split('-')[0] for k in result[0])

            if resultList != []:
                returnList.append((result[1], len(result[0]), resultList, tuple(u)))

        return returnList
    else:
        return None
    

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
        deps.append((token.dep_, token.i, token.head.i))
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

    # x is a list of tuples
    # [((Entity, Entity, Entity, ...), 3, [Dependency Path], (Entity Name, Entity Name, ...))]
    x = shortestDepPath(deps, graph, realNewEntityList, typeList, annoOffnText)
    print(x)
    
    if x != None and x != []:
        
        for item in x:
            # z represents the types of entities combined in this n-uple
            z = '-'.join(map(str, x[0][0]))
            # a represents how many entities are in this n-uple
            a = str(item[1])
            # b represents the named entities
            b = ' '.join(item[-1])
            # c represents the dependency path between the entities
            c = ' '.join(item[2])

            with open("../Data/dataFrames/{0}/{1}.csv".format(a,z), "a") as csvFile:
                d = csv.writer(csvFile)
                d.writerow([b, c])

            with open("../Data/dataFrames/{0}/withSentences/{1}_sent.csv".format(a,z), "a") as sentFile:
                p = csv.writer(sentFile)
                p.writerow([b, c, doc.text])
                  
    
# The masterList comes in a very specific format that looks like the following:
# ['PMID', [('passageType', (passageOffsetAnno, passageTextAnno)), {int(sentNum): [annotation, annotation, ... ]}]]
def myFunct(masterList):
    annoList = list(masterList[1][1].values())[0]
    for i in range(0,len(annoList)+1):
        # Is this actually a powerSet?
        myPowerSet = list(itertools.combinations(annoList, i))
        if len(myPowerSet) > 1:
            makeGraph(masterList[1][0][1], myPowerSet)
