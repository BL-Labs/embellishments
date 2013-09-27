from xml.etree import ElementTree as ET
import re
import os

YEAR_P = re.compile(r"(1[0-9]{3})")

METADATA_ROOT_DIRECTORY = "/mnt/Downloads/md"

MODSXMLNS = "{http://www.loc.gov/mods/v3}"

def get_filepath(identifier):
  return os.path.join(METADATA_ROOT_DIRECTORY, identifier[:4], identifier, "{0}.xml".format(identifier))

def divination_for_year(*items):
  for item in items:
    d = YEAR_P.search(item)
    if d != None:
      return d.groups()[0]    
  return ""

def parse_xml(identifier):
  fp = get_filepath(identifier)
  title, author, pubplace, publisher, pubdate = "","","","",""
  xmlfile = open(fp, "r")
  doc = ET.fromstring(xmlfile.read())
  xmlfile.close()
  mods = doc[0][0][0][0]   # Hacky in a sense, but effective
  titlen = mods.find("{0}titleInfo/{0}title".format(MODSXMLNS))
  nonsort = mods.find("{0}titleInfo/{0}nonSort".format(MODSXMLNS))
  if nonsort != None and nonsort.text != None:
    title += nonsort.text.strip() + " "
  if titlen != None and titlen.text != None:
    title += titlen.text.strip()
  firstauthorn = mods.find('{0}name[@type="personal"]'.format(MODSXMLNS))
  if firstauthorn != None and firstauthorn.text != None:
    authorname = firstauthorn.find('{0}namePart'.format(MODSXMLNS))
    if authorname != None and authorname.text != None:
      author = authorname.text.strip()
    authorterms = firstauthorn.find('{0}namePart[@type="termsOfAddress"]'.format(MODSXMLNS))
    if authorterms != None and authorterms.text != None:
      author += u" {0}".format(authorterms.text.strip())
  oI = mods.find('{0}originInfo'.format(MODSXMLNS))
  pubplacen = oI.find('{0}place/{0}placeTerm'.format(MODSXMLNS))
  if pubplacen != None and pubplacen.text != None:
    pubplace = pubplacen.text.strip()
  publishern = oI.find('{0}publisher'.format(MODSXMLNS))
  if publishern != None and publishern.text != None:
    publisher = publishern.text.strip()
  pubdaten = oI.find('{0}dateIssued'.format(MODSXMLNS))
  if pubdaten != None and pubdaten.text != None:
    pubdate = pubdaten.text.strip()
  guesseddate = divination_for_year(pubdate, pubplace, publisher)
  return identifier, title, author, pubplace, publisher, guesseddate
