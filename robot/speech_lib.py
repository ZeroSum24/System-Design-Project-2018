import os

playmp3 = 'mpg123 -2 '  # standard command to play 2:1 downsample on an mp3 file
all_slots_full_audio = 'slots_full.mp3' # path to audio file
envelope_scanned_audio = 'envelope_scanned.mp3'
deliver_mail_to_audio = 'deliver_mail_to.mp3'

# all slots full
def all_slots_full():
    #os.system(playmp3 + all_slots_full_audio)  # will play the file at all_slots_full_audio
    say_text('all slots full')

# envelope scanned(?)
def envelope_scanned():
    #os.system(playmp3 + envelope_scanned_audio)  #
    say_text('envelope scanned')

#
def deliver_mail_to():
    #os.system(playmp3 + deliver_mail_to_audio)
    say_text('mail delivered')

def say_text(text_input):  # read text with espeak
    os.system('espeak \'' + text_input + '\' --stdout | aplay')


def set_volume(percentage):
    os.system('amixer set Playback,0 ' + str(percentage) + '%')


def get_volume():
    return os.system('amixer get Playback,0')


def beep(frequency, length):
    os.system('beep -f ' + str(frequency) + ' -l ' + str(length))


