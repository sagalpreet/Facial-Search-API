from PIL import Image
from PIL.ExifTags import TAGS
import json

def get_metadata_from_image(path: str) -> str:
    # open image
    img = Image.open(path)

    # extract data
    exifdata = img.getexif()

    meta_dict = {}

    for tid in exifdata:
        # store each tag value pair
        tag_name = TAGS.get(tid, tid)
        tag_value = exifdata.get(tid)
        meta_dict[tag_name] = tag_value
    
    return json.dumps(meta_dict)