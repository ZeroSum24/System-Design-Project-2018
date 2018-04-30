
<body class="stackedit">
  <div class="stackedit__html" align="center"><p><img style="border-radius: 10%;" src="./spam/spam/static/img/logo.png" alt="!spam logo is here">
  </p></div>

[![Codacy  Badge](https://api.codacy.com/project/badge/Grade/4bbe017b71144d10a4cf9061b8144016)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=jcatarino/sdp2018&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.com/jcatarino/sdp2018.svg?token=dEjAyYzexNKMaiz3b5gz&branch=master)](https://travis-ci.com/jcatarino/sdp2018)

# Welcome to the Installation of  <b> <i> !spam </i> </b>

The sections below provide the capability to self-host our software, that is, install  <b> <i> !spam </i> </b> on a custom domain and Ubuntu server. This also allows a custom conversational interface and a custom install on the robot. Note the advanced installation is not recommended for offices without an IT administrator.

Please also note a domain is necessary for issuing an SSL certificate for Google Assistant compatibility.  <b> <i> !spam </i> </b> uses Caddy which in turn uses Let’s Encrypt as Certificate Authority (CA). Certificates are automatically managed, issued and renewed.

### 1. Codebase
To prepare the codebase for the deployment: <b>run $ </b> ```git fork https://github.com/jcatarino/sdp2018.git``` .
From the GitHub website, set the two variables in ```ip.conf``` located in the top directory to the desired domain name and IP address respectively.
You will see the following directories in the repository:

##### /spam:

Contains the code for the server.
Running ```install.sh``` in this directory will install all the components required for the server. It will also start the web server. This should be run after modifying ```ip.conf``` (in step 2).

##### /robot:
Contains the code for the robot.
Running ```install.sh``` in this directory will guide you through the installation of the code onto the robot in the case code modification is desired. This should be run after modifying ```ip.conf``` (in step 2). The script requires a DICE machine to run.

##### /cpp:
Path planning code.
This should not need to be edited. But if it is ,  ```/spam/install.sh``` should be run (refer to the command in section 2.3), to re-compile.

##### /dialogflow.zip:
Optional data for Google Assistant integration.
 See section 3. for installation instructions.


### 2. Setup the server
Follow these steps to prepare the server:
* On the DNS domain manager, add an A record with the target to the server’s IP.
* SSH into the server where you intend to deploy. For detailed instructions, visit https://goo.gl/47rw6n.
* On the SSH session:

  * ```run $ git clone <your repository url>```
  * ```run $ cd sdp2018/spam```
  * ```run $ ./install.sh``` (this may take a few minutes)


* Check the website is accessible using a web browser.

### 3. Setup the Google Assistant App
Creating the Google Assistant App is a straightfoward process. Just read through the following instructions and you will be good to go:
* Create a Dialogflow agent at https://dialogflow.com/
* Click on the settings button → Export and Import → Restore from zip → select sdp2018/dialogflow.zip
* Head to Fulfillment → Enable Webhook → Insert ```https://<your domain>/fulfillment```

### 4. Setup the Office Environment
To change the map layout of the robot, open the configuration file in sdp2018/spam/spam/map.conf
in which paths are defined as follows (note the trailing commas):

```         
<Initial Node> : {<End Node> : (<Distance in cm>, <initial orientation>, <final orientation>),
                  <End Node> :(<Distance in cm>, <initial orientation>, <final orientation>),
		              ...},
```

Specifying each edge in one direction is enough. The distance is measured from the centre of one junction to the centre of another. Orientation is the way in which the robot will be facing relative to the 0° starting point orientation - assuming it is north,  270° would be west. Desks are encoded as 0 distance from a junction and only include the orientations for distinguishing which side of the line they are, eg. 90° for a desk on the east of a line going north. The desk’s final orientation is always the opposite of initial orientation, eg. 270° in this case. Only edit the indicated regions.

After updating the map on the robot, the desks on the server side need to be updated too. Update the list of desks by heading to the website → Settings → Location and their owners by heading to the website → Settings → Staff as shown in 4.1.7.

### 5. Connecting the robot to the internet

The EV3 bricks use Bluetooth to connect to the internet, so we recommend using your phone’s Bluetooth tethering functionality to provide it.

On your device, make sure you are connected to a Wi-Fi or 4G Network. Open the Settings menu and navigate to Hotspot & Tethering to turn Bluetooth tethering on. For more in-depth instructions refer to http://support.google.com/nexus/answer/2812516?hl=en-GB for Android support.
Now for the robot. Turn both bricks on by pressing the centre button on each brick. For each of them, one at a time, do the following:
* Navigate to Wireless and Networks → Bluetooth.
* Check the Powered and Visible checkboxes.
* On the Android device, select “ev3dev” to pair and confirm the passkeys on both devices.
On the EV3 brick, select the phone you just paired with.
* Navigate to Network Connection → Connect.
* Turn on Connect Automatically to do it on boot and make this a one-time setup.
* You should now see on the screen “State: Online” and the bricks IP address above whenever it’s connected.

In case there is a problem with connection, refer to the OS instructions at https://goo.gl/g3Fk4N.

<br/>

### Contact Us:
Thanks for purchasing <b> <i> !spam </i> </b> and checking out our code. Further user information can be be found in the <a href ="docs/group-10-userguide.pdf"> User Guide </a>.

If you have any problems, need support, or need help to install/troubleshoot, contact  <b> <i> !spam </i> </b> at ```support@spamrobot.ml```.

<br/>

<i> Credit to Group 10: <br/>
Alex Shand, Stephen Waddell, Campbell Scott, Grzegorz Wilk, João Catarino, Katie Worton, Rosina Paige 
</i>
