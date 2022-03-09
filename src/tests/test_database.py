from face_recognition import face_encodings, load_image_file
import os
import context

file_dir = os.path.dirname(__file__)

from app.database import Database
from app.metadata import get_metadata_from_image

test_db = Database()

def test_read_config():
    test_db.read_config()
    assert test_db._Database__user == 'cs305'
    assert test_db._Database__password == 'password'
    assert test_db._Database__db_name == 'face_recognition'

def test_connect():
    test_db.connect()
    assert test_db._Database__conn != None

def test_create_table():
    try:
        test_db.create_table('test')
    except:
        pass
    assert test_db._Database__table_name == 'test'

def test_insert_image():
    name = 'George W Bush'
    path = file_dir + '/resources/George_W_Bush_0001.jpg'

    image = load_image_file(path)
    encoding = face_encodings(image)[0]
    metadata = get_metadata_from_image(path)

    test_db.insert_image(name, path, str(list(encoding[:64])), str(list(encoding[64:])), metadata)

def test_identify():
    path = file_dir + '/resources/George_W_Bush_0002.jpg'

    image = load_image_file(path)
    encoding = face_encodings(image)[0]

    val = test_db.identify(str(list(encoding[:64])), str(list(encoding[64:])), 0.6, 2)[0]
    
    assert val[0] == 0.35449545088393986
    assert val[1] == 1
    assert val[2] == 'George W Bush'

def test_get_info():
    id = 1

    val = test_db.get_info(id)

    assert val[0] == 'George W Bush'
    assert val[1] == file_dir + '/resources/George_W_Bush_0001.jpg'
    assert val[2] == '{}'