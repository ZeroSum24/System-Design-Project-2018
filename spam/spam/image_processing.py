# The main function would be replaced but broadly this is
# how the server module should look

#This is the Data Matrix module

from PIL import Image
from pylibdmtx.pylibdmtx import decode

def scanImage(file_path):

    print("Entered image testing")

    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    # scan the image for barcodes
    # return a "Fail" string or a string number if successful
    try:
        codes = decode(image)
        if str(codes) == "[]":
            #Fail State is []
            return "Fail"
        else:
            #Success State is [Decoded(data=b'1', rect=Rect(left=105, top=92, width=-62, height=-62))]
            success_state = str(codes)
            print(success_state)

            _, usr_id, _ = success_state.split("\'")
            print(usr_id)

            return usr_id    # only gets called if the value is an string number





    except AssertionError:
        return "The File is not an image"
        # Throws an exception if its is not an image which we catch and feed back to Flask
