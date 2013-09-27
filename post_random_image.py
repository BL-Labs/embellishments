from redis import Redis
import os
import cv2
from cv2_detect import detect

r = Redis()

root = "/mnt/nas/embellishments"

from photopost import *

from parse_xml import parse_xml

# /static/e/1870/000471167_01_000249_1_Robert Lynne  A novel_1870.jpg
random_image = r.srandmember("images")
filename = random_image.split("/")[-1]
id, vol, page, imgno, _ = filename.split("_",4)

identifier, title, author, pubplace, publisher, guesseddate = parse_xml(id)
decoded = map(lambda x: x.encode("utf-8"), [title, author, guesseddate, pubplace, publisher, vol, str(int(page)), identifier])

tags = ['bldigital', 'bl_labs', 'britishlibrary', guesseddate]

def rect_to_tag(rect_array):
  print rect[0]
  return "_{0}left_{1}top_{2}right_{3}bottom".format(*rect[0])

try:
  img = cv2.imread(os.path.join(root, guesseddate, filename))
  rectlist, hit = detect(img, minSize=(20,20))
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

caption = """<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a> vol {5}, page {6} <em>by {1}</em></p><p>Year: {2}, Place: {3} Publisher: {4}</p>
<p xmlns:dct="http://purl.org/dc/terms/" xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#">
  <a rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <img src="http://i.creativecommons.org/p/zero/1.0/88x31.png" style="border-style: none; height: 31px; width: 88px; float:right;" alt="CC0" />
  </a>
</p>
""".format(*decoded)

if vol == "0":
  caption = """<p>Image from '{0}', <a href="http://explore.bl.uk/primo_library/libweb/action/search.do?cs=frb&doc=BLL01{7}&dscnt=1&scp.scps=scope%3A(BLCONTENT)&frbg=&tab=local_tab&srt=rank&ct=search&mode=Basic&dum=true&tb=t&indx=1&vl(freeText0)={7}&fn=search&vid=BLVU1">{7}</a> page {6} <em>by {1}</em></p><p>Year: {2}, Place: {3} Publisher: {4}</p>
<p xmlns:dct="http://purl.org/dc/terms/" xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#">
  <a rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <img src="http://i.creativecommons.org/p/zero/1.0/88x31.png" style="border-style: none; height: 31px; width: 88px; float:right;" alt="CC0" />
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
    response = api.createPhotoPost(BLOG,post)
    if 'id' in response:
        print response['id']
    else:
        print response
            
except APIError:
    print "Error"
 
print "Done!"

try:
  os.system('gsettings set org.gnome.desktop.background picture-uri "file://{0}"'.format(os.path.join(root, guesseddate, filename)))
except Exception, e:
  print e

