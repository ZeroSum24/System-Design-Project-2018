<!DOCTYPE html>
<html>

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome file</title>
  <link rel="stylesheet" href="https://stackedit.io/style.css" />
</head>

<body class="stackedit">
  <div class="stackedit__html"><p><img src="http://www.relatably.com/m/img/welcome-memes/bb52744768.png" alt="enter image description here"></p>
<h1 id="welcome-travellers-to-the-communication-how-to">Welcome Travellers to the Communication How-to!</h1>
<p>The EV3 brick uses the MQTT protocol to communicate with the Flask App. This app runs locally on the AWS Server. The Broker for the connection is the public IP of the AWS Server (giving us the benefit of a fixed IP <strong>(<em>–pause for gasps–</em>)</strong>).</p>
<h1 id="connecting-the-phone-to-the-ev3">Connecting the Phone to the EV3</h1>
<p>This is for Bluetooth generously granting internet  through the miracles of tethering.</p>
<h2 id="step-1">Step 1:</h2>
<p>Unlock the phone by make a square from the top left downwards. <s>(Often not needed via the kindness of Smart Lock)</s></p>
<h2 id="step-2">Step 2:</h2>
<p>On the EV3, scroll to Wireless and Networks, then Bluetooth, and make sure that Powered, and Visible are both checked</p>
<h2 id="step-3">Step 3:</h2>
<p>On your Android phone turn on Bluetooth</p>
<h2 id="step-4">Step 4:</h2>
<p>Navigate to Tethering &amp; Mobile Hotspot and turn on Bluetooth Tethering</p>
<h2 id="step-5">Step 5:</h2>
<p>On your phone pair with the EV3</p>
<h2 id="step-6">Step 6:</h2>
<p>A confirmation code will appear on both devices, click accept on both.</p>
<h2 id="step-7">Step 7:</h2>
<p>With the devices successfully paired, there should now be a new button to press on on the EV3 screen, Network Connection. You can find this at a later date by going to Wireless and Networks→All Network Connections→SDP’s G3</p>
<h2 id="step-8">Step 8:</h2>
<p>In the new list of options, click Connect, an IP address should now be present on the top left of the EV3 screen (you can also check Connect automatically which will, if possible, connect to this phone when it boots up)</p>
<h1 id="running-flask-on-the-flask-server">Running Flask on the Flask Server</h1>
<p>This is to add more work to the hard toil of the AWS Server. Or to check up on it’s MQTT connection like a hawk.</p>
<h2 id="step-1-sshing">Step 1: SSH’ing</h2>
<p>Ensure you have the <em>SDP_GROUP_KEY.pem</em>: navigate to it in the sockets-testing folder in the flask branch (if not get from Slack). Using the terminal empower it using <code>chmod 400 SDP_GROUP_KEY.pem.txt</code><br>
Then from the same location run <code>ssh -i "SDP_GROUP_KEY.pem.txt" ubuntu@34.251.169.152</code></p>
<h2 id="step-2-running-flask">Step 2: Running Flask</h2>
<p>Run <code>cd sdp2018/spam/spam</code> in the command line. Then run <code>sudo FLASK_APP=spam.py python3 -m flask run --host=127.0.0.1 --port=60</code>. Leave this running please.</p>
<p><s>(Whole step can be avoided if this flask is left running)</s></p>
<h1 id="checking-mqtt-on-the-mqtt-server">Checking MQTT on the MQTT Server</h1>
<p>Our MQTT server needs a job to do too so this is for popping on and checking up on it.</p>
<h2 id="step-1-sshing-1">Step 1: SSH’ing</h2>
<p>Same as before: ensure you have the <em>SDP_GROUP_KEY.pem</em>: navigate to it in the sockets-testing folder in the flask branch (if not get from Slack). Using the terminal empower it using <code>chmod 400 SDP_GROUP_KEY_2.pem.txt</code><br>
Then from the same location run <code>ssh -i "SDP_GROUP_KEY_2.pem.txt" ubuntu@18.219.135.123</code></p>
<h2 id="step-2-checking-mqtt">Step 2: Checking MQTT</h2>
<p>To ensure MQTT is running run <code>systemctl status mosquitto</code>. Press <em>Q</em> to quit this after check.</p>
<h1 id="just-in-case-redundancy-measures"><s>Just In Case</s> Redundancy Measures</h1>
<p>This is just in case our server or brick goes to shit or the apocalypse happens or something along those lines.</p>
<h2 id="install-mqtt-on-the-ev3">Install MQTT on the EV3</h2>
<p>You can publish your file by opening the <strong>Publish</strong> sub-menu and by clicking <strong>Publish to</strong>. For some locations, you can choose between the following formats:</p>
<ul>
<li>Markdown: publish the Markdown text on a website that can interpret it (<strong>GitHub</strong> for instance),</li>
<li>HTML: publish the file converted to HTML via a Handlebars template (on a blog for example).</li>
</ul>
<h2 id="install-mqtt-on-the-servers">Install MQTT on the Servers</h2>
<p>Run this in both servers command lines after ssh’ing individually:<code>sudo apt-get install mosquitto</code>. Check this with <code>systemctl status mosquitto</code>.</p>
<h2 id="install-mqtt-on-the-ev3-1">Install MQTT on the EV3</h2>
<p>This takes literally forever (&gt;2hrs) so <strong>DON’T FLASH THE BRICK</strong>.</p>
<h3 id="step-1-1">Step 1:</h3>
<p>You will need pip3 to install the MQTT module on all devices that are going<br>
to use MQTT: <code>sudo apt-get install python3-pip</code></p>
<h3 id="step-2-1">Step 2:</h3>
<p>Finally: <code>sudo pip3 install paho-mqtt</code></p>
<p><img src="https://img00.deviantart.net/0248/i/2013/295/d/8/that_s_all_folks__by_surrimugge-d6rfav1.png" alt="#That's all folks"></p>
</div>
</body>

</html>
