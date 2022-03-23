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

    str_data = '{}'

    try:
        str_data = json.dumps(meta_dict)
    except:
        try:
            str_data = str(meta_dict)
        except:
            return '{}'
    
    return str_data.replace("'", '"')