import context
from uuid import uuid4
import aiofiles
import os
from face_recognition import load_image_file, face_encodings
from app.database import Database

from fastapi import FastAPI, File, UploadFile, Form

# parameters
TABLE_NAME = 'faces'
FILES = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../..') + '/files')

# setting up app
app = FastAPI()

# setting up database
db = Database()
db.connect()

# creating table (if not exists)
# for storing image encodings
try:
    db.create_table(TABLE_NAME)
except:
    print(f"INFO: Table {TABLE_NAME} already exists")


@app.post("/search_faces/")
async def search_faces(k: float, strictness: float, file: UploadFile = File(..., description="An image file, possible containing multiple human faces.")):
    # TODO: Implement the logic for performing the facial search

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

    # return {"status": "OK", "body": {"matches": [{"id": 112, "person_name": "JK Lal"}]}}
    return {"status": "ERROR", "body": "Not implemented yet"}


@ app.post("/add_face/")
async def add_face(file: UploadFile = File(..., description="An image file having a single human face.")):
    # TODO: Implement the logic for saving the face details in DB
    return {"status": "ERROR", "body": "Not implemented yet"}


@ app.post("/add_faces_in_bulk/")
async def add_faces_in_bulk(file: UploadFile = File(..., description="A ZIP file containing multiple face images.")):
    # TODO: Implement the logic for saving the face details in DB
    return {"status": "ERROR", "body": "Not implemented yet"}


@ app.post("/get_face_info/")
async def get_face_info(api_key: str = Form(...), face_id: str = Form(...)):
    # TODO: Implement the logic for retrieving the details of a face record from DB.
    return {"status": "ERROR", "body": "Not implemented yet"}
