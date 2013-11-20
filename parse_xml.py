from xml.etree import ElementTree as ET
import re
import os

from redis import Redis

r = Redis()

YEAR_P = re.compile(r"(1[0-9]{3})")

METADATA_ROOT_DIRECTORY = "/mnt/Downloads/md"

MODSXMLNS = "{http://www.loc.gov/mods/v3}"

nasmount = "/mnt/nas"

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

def generate_metadata(filename):
  id, vol, page, imgno, _ = filename.split("_",4)
  identifier, title, author, pubplace, publisher, guesseddate = parse_xml(id)
  decoded = map(lambda x: x.encode("utf-8"), [title, author, guesseddate, pubplace, publisher, vol, str(int(page)), identifier])

  # lookup direct links, if any
  # eg to create http://itemviewer.bl.uk/?itemid=lsidyv3bd2589c#ark:/81055/vdc_000000054755.0x000020

  rosetta = r.get("s:"+id)
  if rosetta:
    d, a, u = rosetta.strip().split("\t")
    adjusted_ark_number = "{0:012x}".format(int(a.split("_")[1], 16) - 1)
    adj_ark = "{0}_{1}".format(a.split("_")[0], adjusted_ark_number.upper())
    hexpage = "0x000001"
    try:
      hexpage = "{0:06x}".format(int(page)).upper()
      print hexpage
    except:
      pass
    additional = """
<ul><li>Open the page in the <a href="http://itemviewer.bl.uk/?itemid={2}#{1}.0x{0}">British Library's itemViewer (page: {3})</a></li>
<li><a href="http://access.dl.bl.uk/{2}">Download the PDF for this book</a>
""".format(hexpage, adj_ark, u, page)
    decoded += [additional]
  else:
    decoded += [u""]

  return id, vol, page, imgno, identifier, title, author, pubplace, publisher, guesseddate, decoded
