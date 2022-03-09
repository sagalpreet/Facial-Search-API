from PIL import Image
from PIL.ExifTags import TAGS
import json

def get_metadata_from_image(path: str) -> str:
    img = Image.open(path)
    exifdata = img.getexif()

    meta_dict = {}

    for tid in exifdata:
        tag_name = TAGS.get(tid, tid)
        tag_value = exifdata.get(tid)
        meta_dict[tag_name] = tag_value
    
    return json.dumps(meta_dict)

'''
sql query

create table faces (id serial primary key, name varchar(100), encoding1 cube, encoding2 cube, metadata varchar(2000));

insert into faces (name, encoding1, encoding2, metadata) values (`name`, cube(array`str(list)`), cube(array`str(list)`), `metadata`);

### to check for `input1: str(list)` `input2: str(list)`, `threshold`, `k`

select d1.id, d1.name, sqrt(d1.ed1*d1.ed1 + d2.ed2*d2.ed2) as dis, d1.metadata
from
(select id, name, encoding1 <-> cube(array`input1: str(list)`) as ed1 from faces, metadata) as d1,
(select id, encoding2 <-> cube(array`input2: str(list)`) as ed2 from faces) as d2
where d1.id = d2.id
having dis>`threshold`
order by `dis` desc limit `k`;
'''