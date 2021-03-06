Mechanical Curator: Backend code
================================

Basic flow of events:
---------------------

Based on a set of digitised works (50,000 CC0 Works from 1523-1922: 65,000 zipped volumes of JPG2000 images with an ALTO OCR XML per page)

1 - Using the mighty 'grep', built a list of ALTO xml files that contained at least one 'GraphicalElement'.

2 - Fed the list into a Redis list (via 'load_illustrations.py') which grouped files together so that each list item concerned a single zip file (and so could be opened, all relevant pages processed and closed by a single worker.)

3 - Running 2+ 'snip_embellishments.py' workers, which would pull a job from the queue, and produce snippets in directories (by year), renamed to include some metadata in the filename.

300k+ small (<8in² at 300dpi) illustrations in the collection.

4 - 'load_embellishments.py' pulls in all the collected images so far into a single, large redis set.

5 - Redis's SRANDMEMBER is responsible for pulling out a random image, 'parse_xml' tries to gather up some metadata from the less-than-spectacular metadata and some copy&pasted gist code is used to post to Tumblr. (https://gist.github.com/velocityzen/1242662)

