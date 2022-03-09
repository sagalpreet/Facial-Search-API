import os
import context

file_dir = os.path.dirname(__file__)

from app.metadata import get_metadata_from_image

def test_get_metadata_from_image():
    path=file_dir + "/resources/test_cat.jpg"
    metadata_text=get_metadata_from_image(path)
    assert metadata_text == '{"ResolutionUnit": 1, "YCbCrPositioning": 1, "GPSInfo": 50}'