#!/usr/bin/env python

import spacy


# Define a function that takes in a spaCY doc, source, target, and natural language sentence
# which outputs an appropriately-formatted dependency path between the two
def depList(document, source, target, sentence):

    edges, deps, heads = list()

    for token in document:
        deps.append(token.dep_)
        heads.append(token.head)

        
