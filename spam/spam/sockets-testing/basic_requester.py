import ev3dev.ev3 as ev3
import urllib.request as request

#set-up at the beginning of the control loop. Polling for access to the 
#website before the robot progress commences

#internet connection needs to be established first
#this has to be check by the ev3


#open a loop to a continue until website sends back a confirmation (to be established on the flask end, they will record ip-address of robot at this)
#final website 'http://ec2-34-245-88-253.eu-west-1.compute.amazonaws.com'






#greg's code works by running aslong as no buttons have been pressed on the ev3 brick. It requests the website via the url and decodes the html into a response which if equal to 1 is printed to the screen
website = 'http://127.0.0.1:5000/handle_data'
button = ev3.Button()
while button.any() == False:
    f = request.urlopen(website)
    response = f.read().decode('utf-8') #converts from binary to a string
    if int(response) == 1:
        print('website: ', response)


