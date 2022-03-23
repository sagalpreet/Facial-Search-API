import context
import uvicorn
from uuid import uuid4
import aiofiles
import os, zipfile
from face_recognition import load_image_file, face_encodings
from app.database import Database
from app.metadata import get_metadata_from_image

from fastapi import FastAPI, File, UploadFile, Form

# parameters
TABLE_NAME = 'faces'
FILES = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../..') + '/files')

# setting up app
app = FastAPI()

# setting up database
db = Database()
db.read_config()
db.connect()

# creating table (if not exists)
# for storing image encodings
try:
    db.create_table(TABLE_NAME)
except:
    print(f"INFO: Table {TABLE_NAME} already exists")


@app.post("/search_faces/")
async def search_faces(k: int = Form(...), strictness: float = Form(...), file: UploadFile = File(..., description="An image file, possible containing multiple human faces.")):
    # store image temporarily on file system
    file_path = f'{FILES}/{uuid4()}.jpg'

    # asynchronously read files
    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    # load and encode image
    image = load_image_file(file_path)
    encodings = face_encodings(image)

    res = []

    # collect top k results for each face
    for encoding in encodings:
        res.extend(db.identify(str(list(encoding[:64])), str(list(encoding[64:])), strictness, k))

    # take out the top k results
    res.sort()
    res = res[:k]

    try:
        # remove file stored on server temporarily
        os.remove(file_path)
    except:
        pass

    return {"status": "OK", "body": {"matches": res}}


@ app.post("/add_face/")
async def add_face(file: UploadFile = File(..., description="An image file having a single human face.")):
    if (file.content_type != 'image/jpeg'):
        return {"status": "ERROR", "body": "Only jpg formats supported"}

    # get the name of the person from filename
    name = file.filename

    if (name[-4] == '.'):
        # .jpg format
        name = name[:-4]
    else:
        # .jpeg format
        name = name[:-5]

    # store image on file system
    file_path = f'{FILES}/{uuid4()}.jpg'

    # asynchronously read file
    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    # load and encode image
    try:
        image = load_image_file(file_path)
        encoding = face_encodings(image)[0]
        metadata = get_metadata_from_image(file_path)
    except:
        return {"status": "ERROR", "body": "Image not detected"}

    try:
        db.insert_image(name, file_path, str(list(encoding[:64])), str(list(encoding[64:])), metadata)
        return {"status": "OK", "body": "Image added"}
    except:
        return {"status": "ERROR", "body": "Insertion Failed"}


@ app.post("/add_faces_in_bulk/")
async def add_faces_in_bulk(file: UploadFile = File(..., description="A ZIP file containing multiple face images.")):
    if (file.content_type != 'application/zip'):
        return {"status": "ERROR", "body": "Only zip formats supported"}

    # store images on file system
    file_path = f'{FILES}/{uuid4()}.zip'
    directory = file_path[:-4]

    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    # extract zip
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(directory)

    # get bulk load object
    bulk_load = db.bulk_insert()

    for root, _, files in os.walk(directory):
        if (not files):
            # check if no file is there
            continue

        # get the name of the person from parent directory
        name = os.path.basename(root)

        for file_name in files:
            image_path = f'{root}/{file_name}'

            # load and encode image, get metadata for it
            try:
                image = load_image_file(image_path)
                encoding = face_encodings(image)[0]
                metadata = get_metadata_from_image(image_path)
            except:
                continue

            # convert encodings into strings
            e1 = str(list(encoding[:64]))
            e2 = str(list(encoding[64:]))

            try:
                bulk_load.insert_image(name, image_path, e1, e2, metadata)
            except:
                # rollback if transaction fails
                bulk_load.rollback()
                return {"status": "ERROR", "body": "Insertion Failed"}

    # commit if successful
    bulk_load.commit()
    return {"status": "OK", "body": "Image added"}


@ app.post("/get_face_info/")
async def get_face_info(api_key: str = Form(...), face_id: str = Form(...)):
    # retrieve info from database
    info = db.get_info(face_id)

    if (info == None):
        return {"status": "ERROR", "body": "Invalid face id"}

    return {"status": "OK", "body": info}

# the following code can be uncommented to run server from the file itself
'''
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")
'''