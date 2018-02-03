import ev3dev.ev3 as ev3
import urllib.request as request


website = 'https://homepages.inf.ed.ac.uk/s1504889/SDP/'
button = ev3.Button()
while button.any() == False:
    f = request.urlopen(website)
    response = f.read().decode('utf-8') #converts from binary to a string
    if int(response) == 1:
        print('website: ', response)
