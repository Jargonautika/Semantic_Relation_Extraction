#!/usr/bin/python3
import csv
import time
import requests

from lxml import etree as ET
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Accepts an integer as a possiblePMID which is then sent to access the RESTful API from NIH
def main(possiblePMID, writer):
    
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    r = session.get("https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/Bioconcept/{}/BioC/".format(possiblePMID))
    if r.status_code == 200:
        outFile = open('../Data/PMID_List_Master-2018.08.25.csv', 'a', newline = '')
        writer = csv.writer(outFile, delimiter=",")
        writer.writerow([possiblePMID, ''])

outFile = open('../Data/PMID_List_Master-2018.08.27.csv', 'w', newline = '')
writer = csv.writer(outFile, delimiter=",")
writer.writerow(['PMID_List'])  
outFile.close()


for x in range(2000000, 3000000):
    print(x)
    main(x, writer)

