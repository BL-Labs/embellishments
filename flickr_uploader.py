import time
import os, sys, re
from redis import Redis

from parse_xml import parse_xml

embellishments_path = "/mnt/nas/embellishments"

r = Redis()

wq = "uploadq"
output = "coveroutput"

def get_job(workerid):
  if r.llen(workerid) == 0:
    status = ""
    while(status == ""):
      status = r.rpoplpush(wq, workerid)
      if status == "":
        r.lrem(workerid, job, 1)
    return status
  else:
    return r.lrange(workerid, 0, 0)[0]

def clear_job(workerid, job):
  r.lrem(workerid, job, 1)

# Flickr details

import flickr_api
a = flickr_api.auth.AuthHandler.load("BLLibraryAuth")
flickr_api.set_auth_handler(a)

if __name__ == "__main__":
  workerid = "uploadwrk"+sys.argv[1]
  while(True):
    job = get_job(workerid)
    while(job):
      if job != "":
        img = job.strip()
        location = os.path.join(embellishments_path, img)
        # get id
        id, vol, page, _ = img.split("/",1)[1].split("_",3)
        metadata = parse_xml(id)
        """
  Arguments:
        photo_file
            The file to upload.
        title (optional)
            The title of the photo.
        description (optional)
            A description of the photo. May contain some limited HTML.
        tags (optional)
            A space-seperated list of tags to apply to the photo.
        is_public, is_friend, is_family (optional)
            Set to 0 for no, 1 for yes. Specifies who can view the photo.
        safety_level (optional)
            Set to 1 for Safe, 2 for Moderate, or 3 for Restricted.
        content_type (optional)
            Set to 1 for Photo, 2 for Screenshot, or 3 for Other.
        hidden (optional)
            Set to 1 to keep the photo in global search results, 2 to hide
            from public searches.
        async
            set to 1 for async mode, 0 for sync mode
        """

        identifier, title, author, pubplace, publisher, guesseddate = metadata
        decoded = map(lambda x: x.encode("utf-8"), [title, author, guesseddate, pubplace, publisher, vol, str(int(page)), identifier])

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
            uploaded_title=u"Image taken from page {1} of '{0}'".format(decoded[0].decode("utf-8"), page.decode("utf-8"))
            try:
              uploaded_title = u"Image taken from page {1} of '{0}'".format(decoded[0].decode("utf-8"), str(int(page)).decode("utf-8"))
            except:
              pass
            uploaded = flickr_api.upload(photo_file=location,
                            title=uploaded_title,
                            description = desc.decode("utf-8"),
                            tags=u"bldigital date:{0} pubplace:{1} public_domain mechanicalcurator".format(decoded[2].decode("utf-8"), re.sub(" ", "_", decoded[3].decode("utf-8"))),
                            is_public=1, is_friend=1, is_family=1,
                            content_type="photo", hidden=0, async=0)
            r.lpush("uploaded", "{0}\t{1}".format(location, str(uploaded.id)))
            print("http://www.flickr.com/photos/mechanicalcuratorcuttings/{0} uploaded".format(str(uploaded.id)))
            clear_job(workerid, job)
          except flickr_api.FlickrError,e:
            print "Flickr Error"
            print e
            from datetime import datetime
            r.lpush("uploaderror", "{0}\t{2}\t{1}".format(job, str(e), datetime.now().isoformat()))
            r.lpush("failedupload", job)
            clear_job(workerid, job) 
      else:
        clear_job(workerid, job)
      job = get_job(workerid)
    print("%s ran out of jobs - waiting for 5 seconds before checking again" % workerid)
    time.sleep(5)
