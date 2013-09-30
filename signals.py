from cv2_detect import *

from Levenshtein import distance

from parse_xml import parse_xml

CV_SIGNALS = [slantyness, bubblyness, aspectratio]

MOOD = {'metadata': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        'cv_signals': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]} 

SIGNAL_NAMES = ["identifier",
                "title",
                "author",
                "pubplace", 
                "publisher", 
                "guesseddate",
                "slantyness",
                "bubblyness_size",
                "bubblyness_avesize",
                "bubblyness_x",
                "bubblyness_y",
                "hbias",
                "vbias"]

def breakdown_imagename(filename):
  id, vol, page, imgno, _ = filename.split("_",4)
  return id, vol, page, imgno

def gather_signals(filepath):
  filename = filepath.split("/")[-1]
  id, vol, page, imgno = breakdown_imagename(filename.split("/")[-1])
  metadata = parse_xml(id)
  cv_signals = []
  for cv_measure in CV_SIGNALS:
    signal = cv_measure(filepath)
    if isinstance(signal, tuple):
      cv_signals.extend(signal)
    else:
      cv_signals.append(signal)
  return {'metadata': metadata,
          'identifier': (id, vol, page, imgno),
          'cv_signals': cv_signals}

def compare_metadata(prev, potential, mood):
  linked = zip(prev['metadata'], potential['metadata'])
  diffs = map(lambda x: distance(x[0], x[1]), linked)
  weighted_diffs = map(lambda x: x[0]*x[1], zip(diffs, mood['metadata']))
  return weighted_diffs

def compare_cv(prev, potential, mood):
  figures = []
  deltas = [np.abs(a-b)*c for a,b,c in zip(prev['cv_signals'], potential['cv_signals'], mood['cv_signals'])]
  return deltas
    

def signal_combine(comparison):
  return sum(comparison)

def compare(previous_img_path, potential_img_path, mood=MOOD):
  prev = gather_signals(previous_img_path)
  potential = gather_signals(potential_img_path)
  md_comparison = compare_metadata(prev, potential, mood)
  cv_comparison = compare_cv(prev, potential, mood)
  return zip(SIGNAL_NAMES, md_comparison+cv_comparison)
