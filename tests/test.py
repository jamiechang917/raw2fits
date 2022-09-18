import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from pprint import pprint
from image import *
import exifread

path = "tests/img/test.CR2"

img = Image(path)
img.save_fits("LIGHT", path=os.getcwd())

# exif = exifread.process_file(open(path, 'rb'))
# for k,v in exif.items():
#     if k != "JPEGThumbnail":
#         print(f"{k}:\t\t\t\t{v}")
