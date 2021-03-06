from redis import Redis
import os, sys
import cv2
from cv2_detect import detect

SIMILARITY_THRESHOLD = 5.0

adryrun = False

r = Redis()

from parse_xml import parse_xml, generate_metadata, nasmount
root = os.path.join(nasmount, "embellishments")

from photopost import *
from signals import compare as img_compare


def rect_to_tag(rect_array):
  return "_{0}left_{1}top_{2}right_{3}bottom".format(*rect[0])

def generate_caption_html(vol, decoded):
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
  return caption
  

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

    id, vol, page, imgno, identifier, title, author, pubplace, publisher, guesseddate, decoded = generate_metadata(filename)

    tags = ['bldigital', 'bl_labs', 'britishlibrary', guesseddate]

    # Similarity checks

    tumblr_id = 0
    previous_image = r.lrange("previousimages", 0, -1)
    if "\t" in previous_image[0]:
      previous_image, tumblr_id = previous_image[0].split("\t")

    if previous_image.startswith("/mnt/nas/embellishments"):
      previous_image = os.path.join(root, previous_image[len("/mnt/nas/embellishments")+1:])

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

if __name__ == "__main__":
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

  caption = generate_caption(vol, decoded)
 
  print("Uploading {0}".format(filename))
  print(caption)
  
  print("\n Tags: " + ",".join(map(lambda x: "#"+x, tags)))

  from tumblr_keys import *

  # keys from above:
  #CONSUMER_KEY = ''
  #CONSUMER_SECRET = '' 
  #OAUTH_TOKEN = '' 
  #OAUTH_TOKEN_SECRET = ''
   
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
  
