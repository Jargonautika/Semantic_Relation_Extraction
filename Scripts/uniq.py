#!/usr/bin/env python

import os
import glob

for f in glob.glob("../Data/dataFrames/*/*/*"):
    uniqueList = list()
    basename = os.path.basename(f)
    pathname = os.path.dirname(f)
    print(basename)
    
    if basename != 'withSentences' and basename != 'sorted':
        with open(f, 'r') as infile:
            for line in infile:
                if line not in uniqueList:
                    uniqueList.append(line)
            if not os.path.exists(pathname + '/sorted/'):
                os.makedirs(pathname + '/sorted/')
            outfile = open(pathname + '/sorted/' + basename[:-4] + '-sorted.csv', 'w')
            outfile.writelines(sorted(uniqueList))
