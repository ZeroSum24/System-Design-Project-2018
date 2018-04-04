import os

playmp3 = 'mpg123 -2 '  # standard command to play 2:1 downsample on an mp3 file
all_slots_full_audio = 'slots_full.mp3' # path to audio file
envelope_scanned_audio = 'envelope_scanned.mp3'
deliver_mail_to_audio = 'deliver_mail_to.mp3'

def ready_for_loading():
    #say_mp3('./speech_lib/insert.mp3')
    say_text('Ready for loading')

# audio to play when panicking
def panicking():
    #say_mp3('./speech_lib/error.mp3')
    say_text('An error has occurred. Assistance needed.')

# obstacle detected
def obstacle_detected():
    #say_mp3('./speech_lib/obstacle.mp3')
    say_text('Obstacle detected.')

# all slots full
def all_slots_full():
    #os.system(playmp3 + all_slots_full_audio)  # will play the file at all_slots_full_audio
    #say_mp3('./speech_lib/full.mp3')
    say_text('all slots full')

# envelope scanned(?)
def envelope_scanned():
    #os.system(playmp3 + envelope_scanned_audio)  #
    #say_mp3('./speech_lib/scanned.mp3')
    say_text('envelope scanned')

def please_insert_envelope():
    #say_mp3('./speech_lib/insert.mp3')
    say_text('Please insert envelope')

def deliver_mail_to():
    #say_mp3('./speech_lib/delivered.mp3')
    #os.system(playmp3 + deliver_mail_to_audio)
    say_text('mail delivered')

def say_mp3(fname):
    os.system('mpg123 {}'.format(fname))

def say_text(text_input):  # read text with espeak
    os.system("espeak '" + text_input + "' --stdout | aplay")

def set_volume(percentage):
    os.system('amixer set Playback,0 ' + str(percentage) + '% > /dev/null 2>&1') # and supressing the output

def get_volume():
    return os.system('amixer get Playback,0')

def beep(frequency, length):
    os.system('beep -f ' + str(frequency) + ' -l ' + str(length))

set_volume(100) # sets volume on importing the module
