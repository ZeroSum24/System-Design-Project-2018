#This is the Image Processing module which scans Data Matrix

from PIL import Image
from pylibdmtx.pylibdmtx import decode

def scanImage(file_path):

    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    # Scan the image for barcodes
    # Returns a "Fail" string or a string number if successful
    try:
        codes = decode(image)
        if str(codes) == "[]":
            # Fail State is []
            return "Fail"
        else:
            # Success State is [Decoded(data=b'1', rect=Rect(left=105, top=92, width=-62, height=-62))]
            success_state = str(codes)
            print(success_state)

            _, usr_id, _ = success_state.split("\'")
            print(usr_id)

            return usr_id    # Only gets called if the value is an string number

    except AssertionError:
        return "The File is not an image"
        # Throws an exception if its is not an image which we catch and feed back to Flask
