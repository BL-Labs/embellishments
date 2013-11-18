from redis import Redis
import os, sys
import cv2
from cv2_detect import detect

SIMILARITY_THRESHOLD = 5.0

adryrun = False

r = Redis()

root = "/mnt/nas/embellishments"

from photopost import *
from signals import compare as img_compare

from parse_xml import parse_xml

def rect_to_tag(rect_array):
  return "_{0}left_{1}top_{2}right_{3}bottom".format(*rect[0])

def post_not_so_random_image(imagename=""):
  connected_attempts = 8
  if imagename:
    connected_attempts = 1
  while(connected_attempts >= 1):
    print("Attempts: {0}".format(connected_attempts))
    # /static/e/1870/000471167_01_000249_1_Robert Lynne  A novel_1870.jpg
    if not imagename:
      random_image = r.srandmember("images")
    else:
      random_image = imagename

    filename = random_image.split("/")[-1]
    print("Assessing {0} for suitability".format(filename))
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

    tags = ['bldigital', 'bl_labs', 'britishlibrary', guesseddate]

    # Similarity checks

    tumblr_id = 0
    previous_image = r.lrange("previousimages", 0, -1)
    if "\t" in previous_image[0]:
      previous_image, tumblr_id = previous_image[0].split("\t")
    connections = []
    try:
      if previous_image:
        comparison = img_compare(previous_image, os.path.join(root, guesseddate, filename))
        for tagname, rating in comparison:
          if rating < SIMILARITY_THRESHOLD:
            print("Similar to previous! by '{0}' --- {1}".format(tagname, rating))
            tags.append("similar_to_{1}_{0}".format(tagname, str(tumblr_id)))
            connections.append(tagname)
      if len(connections) >= 3 or 'title' in connections or 'publisher' in connections or 'pubplace' in connections:
        connected_attempts = 1
      elif connected_attempts == 1:
        # unconnected, but 'timed out'
        tags.append("new_train_of_thought")
      connected_attempts -= 1
    except Exception, e:
      print("FAILED: {0}".format(e))
  return id, vol, page, imgno, identifier, title, author, pubplace, publisher, guesseddate, decoded, tags, filename


if len(sys.argv) == 2:
  suggested_img = sys.argv[1]
  if r.sismember("images", "/static/e/"+suggested_img):
    print("Using '{0}'".format(suggested_img))
    filename = suggested_img.split("/")[1]
    id, vol, page, imgno, identifier, title, author, pubplace, publisher, guesseddate, decoded, tags, filename = post_not_so_random_image("/static/e/"+suggested_img)
else:
  id, vol, page, imgno, identifier, title, author, pubplace, publisher, guesseddate, decoded, tags, filename = post_not_so_random_image()

try:
  img = cv2.imread(os.path.join(root, guesseddate, filename))
  rectlist, hit = detect(img, minSize=(60,60), scaleFactor=1.3, minNeighbors=5)
  if hit:
    for match in rectlist.keys():
      if rectlist[match] != []:
        rect = rectlist[match].tolist()
        orientation, haar = match.split("_")
        tag = ""
        if orientation == "r":
          tag += "sideways_"
          rect = [[ rect[0][1], img.shape[1] - rect[0][0], rect[0][3], img.shape[1] - rect[0][2] ]]
        tag += haar+"_detected"+rect_to_tag(rectlist[match])
        tags.append(tag)
except KeyError:
  print("Whoops")

caption = """<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a></p>
<ul>
  <li><strong>Author:</strong> {1}</li>
  <li><strong>Volume:</strong> {5}</li>
  <li><strong>Page:</strong> {6}</li>
  <li><strong>Year:</strong> {2}</li>
  <li><strong>Place:</strong> {3}</li>
  <li><strong>Publisher:</strong> {4}</li>
</ul>
<p><em>Following the link above will take you to the British Library's integrated catalogue. You will be able to download a PDF of the book this image is taken from, as well as view the pages up close with the 'itemViewer'. Click on the 'related items' to search for the electronic version of this work.</em></p>{8}
<p xmlns:dct="http://purl.org/dc/terms/" xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#">
  <a rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <img class="cczero" src="http://i.creativecommons.org/p/zero/1.0/88x31.png" alt="CC0" />
  </a>
</p>
""".format(*decoded)

if vol == "0":
  caption = """<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a></p>
<ul>
  <li><strong>Author:</strong> {1}</li>
  <li><strong>Page:</strong> {6}</li>
  <li><strong>Year:</strong> {2}</li>
  <li><strong>Place:</strong> {3}</li>
  <li><strong>Publisher:</strong> {4}</li>
</ul>
<p><em>Following the link above will take you to the British Library's integrated catalogue. You will be able to download a PDF of the book this image is taken from, as well as view the pages up close with the 'itemViewer'. Click on the 'related items' to search for the electronic version of this work.</em></p>{8}
<p xmlns:dct="http://purl.org/dc/terms/" xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#">
  <a rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <img class="cczero" src="http://i.creativecommons.org/p/zero/1.0/88x31.png" alt="CC0" />
  </a>
</p>
""".format(*decoded)

print("Uploading {0}".format(filename))
print(caption)

print("\n Tags: " + ",".join(map(lambda x: "#"+x, tags)))

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''
 
BLOG = 'mechanicalcurator.tumblr.com'
 
api = TumblrAPIv2(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
 
date  = time.gmtime()
post = {
        'type' : 'photo',
        'date' : time.strftime ("%Y-%m-%d %H:%M:%S", date),
        'data' : os.path.join(root, guesseddate, filename),
        'tags' : ",".join(tags),
        'caption' : caption
}
 
try:
  if not adryrun:
    response = api.createPhotoPost(BLOG,post)
    if 'id' in response:
        print response['id']
        post = {'caption': caption,
            'tags':tags,
            'response': response,
            'id': identifier,
            'year': guesseddate,
            'filename': filename}
        r.lpush("posted", json.dumps(post))
        r.lpush("previousimages", "\t".join([os.path.join(root, guesseddate, filename), str(response['id'])]))
    else:
        print response
            
except APIError:
    print "Error"
 
print "Done!"


try:
  os.system('gsettings set org.gnome.desktop.background picture-uri "file://{0}"'.format(os.path.join(root, guesseddate, filename)))
except Exception, e:
  print e

