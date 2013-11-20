
import time
import os, sys, re
from redis import Redis

from parse_xml import parse_xml

embellishments_path = "/mnt/nas/embellishments"

r = Redis()

wq = "uploadq"
output = "coveroutput"

# Flickr details

import flickr_api
import flickr_api.api
a = flickr_api.auth.AuthHandler.load("BLLibraryAuth")
flickr_api.set_auth_handler(a)


def get_md(item):
  job, flickr_id = item.strip().split("\t")
  img = job.strip()[24:]
  location = os.path.join(embellishments_path, img)
  id, vol, page, _ = img.split("/",1)[1].split("_",3)
  metadata = parse_xml(id)
  identifier, title, author, pubplace, publisher, guesseddate = metadata
  decoded = map(lambda x: x.encode("utf-8"), [title, author, guesseddate, pubplace, publisher, vol, str(int(page)), identifier])
  
  uploaded_title=u"Image taken from page {1} of '{0}'".format(decoded[0].decode("utf-8"), page.decode("utf-8"))
  try:
    uploaded_title = u"Image taken from page {1} of '{0}'".format(decoded[0].decode("utf-8"), str(int(page)).decode("utf-8"))
  except:
    pass

  if os.path.exists(location):
    try:
      rosetta = r.get("s:"+id)
      if rosetta:
        d, a, u = rosetta.strip().split("\t")
        adjusted_ark_number = "{0:012x}".format(int(a.split("_")[1], 16) - 1)
        adj_ark = "{0}_{1}".format(a.split("_")[0], adjusted_ark_number.upper())
        hexpage = "0x000001"
        try:
          hexpage = "{0:06x}".format(int(page)).upper()
        except:
          pass
        additional = """
<ul><li>Open the page in the <a href="http://itemviewer.bl.uk/?itemid={2}#{1}.0x{0}">British Library's itemViewer (page: {3})</a></li>
<li><a href="http://access.dl.bl.uk/{2}">Download the PDF for this book</a>
""".format(hexpage, adj_ark, u, page)
        decoded += [additional]
      else:
        decoded += [u""]
    except Exception, e:
      print e

  desc = """
<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a></p>
<ul>
  <li><strong>Author:</strong> {1}</li>
  <li><strong>Volume:</strong> {5}</li>
  <li><strong>Page:</strong> {6}</li>
  <li><strong>Year:</strong> {2}</li>
  <li><strong>Place:</strong> {3}</li>
  <li><strong>Publisher:</strong> {4}</li>
</ul>
<p><em>Following the link above will take you to the British Library's integrated catalogue. You will be able to download a PDF of the book this image is taken from, as well as view the pages up close with the 'itemViewer'. Click on the 'related items' to search for the electronic version of this work.</em></p>{8}
""".format(*decoded)
  if vol == "0":
    desc = """
<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a></p>
<ul>
  <li><strong>Author:</strong> {1}</li>
  <li><strong>Page:</strong> {6}</li>
  <li><strong>Year:</strong> {2}</li>
  <li><strong>Place:</strong> {3}</li>
  <li><strong>Publisher:</strong> {4}</li>
</ul>
<p><em>Following the link above will take you to the British Library's integrated catalogue. You will be able to download a PDF of the book this image is taken from, as well as view the pages up close with the 'itemViewer'. Click on the 'related items' to search for the electronic version of this work.</em></p>{8}
""".format(*decoded)
  
  return flickr_id, uploaded_title, desc

photomd = {}
for item in r.lrange("uploaded", 0, -1):
  fid, t, d = get_md(item)
  photomd[fid] = (t,d.decode('utf-8'))


counter = 1
page = 1

photos = user.getPhotos(page)

while(photos):
  for photo in photos:
    if photomd.has_key(photo.id):
      t,d = photomd[photo.id]
      photo.setMeta(title=t.encode('utf-8'), description=d.encode('utf-8'))
      counter += 1
  page += 1
  photos = user.getPhotos(page = page)
  print("Updating page {0}".format(page))

