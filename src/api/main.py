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
async def search_faces(k: float = Form(...), strictness: float = Form(...), file: UploadFile = File(..., description="An image file, possible containing multiple human faces.")):
    # store image temporarily on file system
    file_path = f'{FILES}/{uuid4()}.jpg'

    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    image = load_image_file(file_path)
    encodings = face_encodings(image)

    res = []

    for encoding in encodings:
        res.extend(db.identify(str(list(encoding[:64])), str(list(encoding[64:])), strictness, k))

    res.sort(reverse=True)
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

    name = file.filename

    if (name[-3] == '.'):
        # .jpg format
        name = name[:-3]
    else:
        # .jpeg format
        name = name[:-4]

    # store image on file system
    file_path = f'{FILES}/{uuid4()}.jpg'

    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    image = load_image_file(file_path)
    encoding = face_encodings(image)
    metadata = get_metadata_from_image(file_path)

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
    directory = file_path[-3]

    async with aiofiles.open(file_path, 'wb') as temp_file:
        content = await file.read()
        await temp_file.write(content)

    # extract zip
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(directory)

    for root, _, files in os.walk(directory):
        if (not files):
            continue

        name = os.path.basename(root)

        for file_name in files:
            image_path = f'{root}/{name}'

            image = load_image_file(image_path)
            encoding = face_encodings(image)
            metadata = get_metadata_from_image(image_path)

        try:
            db.insert_image(name, str(list(encoding[:64])), str(list(encoding[64:])), metadata, False)
        except:
            return {"status": "ERROR", "body": "Insertion Failed"}

    db.commit()
    return {"status": "OK", "body": "Image added"}


@ app.post("/get_face_info/")
async def get_face_info(api_key: str = Form(...), face_id: str = Form(...)):
    info = db.get_info(face_id)

    if (info == None):
        return {"status": "ERROR", "body": "Invalid face id"}

    return {"status": "OK", "body": info}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")