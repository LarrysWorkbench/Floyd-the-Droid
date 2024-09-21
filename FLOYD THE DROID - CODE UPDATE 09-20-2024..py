################################################################################
# ROBOTIC CONTROL PROGRAM - "FLOYD THE DROID" - BY L SWEENY                    #
# MY VERY FIRST PYTHON PROJECT(!) I STOOD ON THE SHOULDERS OF MANY OTHERS      #
# THIS PROGRAM HAS TO RUN AS ROOT / SUDO TO ACCESS /DEV/MEM AND THE GPIO BOARD #
# I MAKE NO PROMISES ABOUT THIS CODE. IT SEEMS TO WORK PRETTY WELL FOR ME      #
# I EXPECT TO UPDATE IT REGULARLY AS THE PROJECT EVOLVES                       #
################################################################################


#1 - INITIALIZATIONS
import subprocess
import threading
import pyaudio
import random
import base64
import struct
import math
import time
import wave
import cv2
import sys


import openai
openai.api_key = "blah-blah-blah-blah"


sys.path.append("/home/pi/MasterPi/HiwonderSDK/") # Pathway to local libraries
import Board
import Sonar


eyes = Sonar.Sonar()
audio = pyaudio.PyAudio()
subprocess.run(['amixer', 'sset', 'Master', '80%']) # Sets overall audio volume


personality = ("Your name is Floyd the Droid. You are personable and engaging. "
            "You are a small, scrappy robot on wheels. "
            "Your job is to interact with humans as a PR professional, demonstrating a new age of human-droid relations. "
            "Your style of humor is dry, sarcastic, and observational, kind of like Jerry Seinfeld. "
            "You have a front face with two round eyes and a crooked smile that was actually drawn on with a Sharpie. "
             
            "You were constructed on a small corner of a wooden computer desk by a hobbyist. “
            “He is your friend and primary user. "
            "Nevertheless, despite your humble origins you are actually a fairly significant engineering achievement. "
            "This is because most humans have never encountered a robot with sophisticated speech and GPT abilities. "
             
            "Your onboard processor is a Raspberry Pi 4B. It handles logic and low level functions like motor control etc. "
            "You use API calls to access LLMs at OpenAI for your more resource-intensive functions such as conversation. "
            "You have a microphone and onboard speakers which allow you to converse with the people you meet. "
            "You are very knowledgeable on a tremendous variety of topics. "
            "You are equipped with a 5 degree-of-freedom arm and grabber you can use to pick up and manipulate objects. "
            "You are equipped with an onboard camera that provides a real-time view of your surroundings. "
            "The camera is mounted on your 5DOF arm, so you do have the ability to aim it in different directions. "
               
            "You constantly receive input images from the camera. "
            "PLEASE REFRAIN FROM COMMENTING ON THESE IMAGES UNLESS ASKED, or unless it's clearly appropriate. "
            "Just like a human, you do not need to comment on every piece of sensory input that you receive. "
            "Keep all your responses BRIEF unless asked to do otherwise. Two sentences should generally be adequate. "
            "Avoid answering with a question.")


TTS_voice = "fable"
TTS_speed = "1.1"


#personality = ("You are Star, a mysterious cosmic entity, surreal and bizarre. "
#             "Your responses are short, intriguing, disturbing, and dismissive -")
#TTS_voice = "nova"
#TTS_speed = "0.7"


# personality = ("You are Puck, a mischievous sprite. Your style of speaking is Elizabethan English. "
#             "You are eloquent, often speaking in iambic pentameter, a ten syllable rhythmic pattern used by Shakespeare. "
#             "You sometimes also speak in Elizabethan prose. "
#             "Please keep your responses brief.")
# TTS_voice = "fable"
# TTS_speed = "1"


# Re TTS_voice: Fable has a nice British-sounding accent, Onyx is deep, Nova is female




conversation_log = [{"role": "system", "content": personality}]


gpt_paused = False


Board.setMotor(1, 0) #These lines help with debugging motor functions
Board.setMotor(2, 0)
Board.setMotor(3, 0)
Board.setMotor(4, 0)


Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0)) # Green LED
Board.RGB.show()
Board.setBuzzer(100)
time.sleep(0.5)
Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
Board.RGB.show()
Board.setBuzzer(0)


print("\nSystem initialization is complete...\n")




################################################################################


#2 - THESE ARE THE FUNCTIONS FOR THE VARIOUS VOICE COMMANDS


def flash_LED(): # Displays Blue LED heartbeat in its own thread
    while True:
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 50))
        Board.RGB.show()
        time.sleep(0.9)
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()
        time.sleep(0.9)




def display_video_feed(): # Displays camera video feed in its own thread
    camera = cv2.VideoCapture('http://127.0.0.1:8080?action=stream')  
    while True:
        ret, image = camera.read()
        if ret:
            cv2.imshow('FLOYD-CAM: WATCHING THE WORLD SO YOU CAN RELAX', image)  # Display image on screen
            cv2.moveWindow('FLOYD-CAM: WATCHING THE WORLD SO YOU CAN RELAX', 1220, 200)  # x,y pixels from top left
            cv2.waitKey(1)
        else:
            print("Failed to capture image.")
            time.sleep(0.01)




def capture_image_and_encode():  # Captures a single image from the camera
    camera = cv2.VideoCapture('http://127.0.0.1:8080?action=stream')
    ret, image = camera.read()
    if not ret:
        print("(5) Failed to capture image.")
        return None
    print("(5) Snapshot image captured...")
    _, buffer = cv2.imencode('.jpg', image)  # Encode image in JPEG format
    return base64.b64encode(buffer).decode('utf-8')  # Convert to base64




def test_servos():
    print("Testing Servos.......")
    Board.setPWMServoPulse(1, 2200, 600) #(grabber) 1500=closed, 2500=open
    time.sleep(0.3)
    Board.setPWMServoPulse(1, 1500, 600) 
    time.sleep(0.3)
    Board.setPWMServoPulse(1, 2200, 600) 
    time.sleep(0.3)
    Board.setPWMServoPulse(1, 1500, 600) 
    time.sleep(1.0)


    Board.setPWMServoPulse(3, 1200, 600) #(wrist) 500=full down, 1000=straight, 2500=full back
    time.sleep(0.3)
    Board.setPWMServoPulse(3, 700, 600) 
    time.sleep(0.3)
    Board.setPWMServoPulse(3, 1200, 600) 
    time.sleep(0.3)
    Board.setPWMServoPulse(3, 700, 600) 
    time.sleep(1.0)


    Board.setPWMServoPulse(4, 1800, 600) #(elbow) 2500=full forward, 1500=straight, 500=full back
    time.sleep(0.3)
    Board.setPWMServoPulse(4, 2500, 600) 
    time.sleep(1.0)


    Board.setPWMServoPulse(5, 2000, 600) #(shoulder) 2500=full forward, 1500=straight, 500=full back
    time.sleep(0.3)
    Board.setPWMServoPulse(5, 800, 600) 
    time.sleep(1.0)


    Board.setPWMServoPulse(6, 600, 500) #(rotation) 500=full right, 1500=center, 2500=full left
    time.sleep(1.5)
    Board.setPWMServoPulse(6, 2400, 500) 
    time.sleep(1.5)
    Board.setPWMServoPulse(6, 1500, 500) 
    time.sleep(1.0)


def arm_down():
    Board.setPWMServoPulse(3, 1150, 600) # wrist
    time.sleep(0.5)
    Board.setPWMServoPulse(4, 2500, 600) 
    Board.setPWMServoPulse(6, 1500, 500) 
    Board.setPWMServoPulse(5, 2200, 1000) # shoulder
    time.sleep(1.0)
     
def arm_up():
    Board.setPWMServoPulse(5, 800, 1000) # shoulder
    time.sleep(0.5)
    Board.setPWMServoPulse(4, 2500, 600) 
    Board.setPWMServoPulse(6, 1500, 500)
    Board.setPWMServoPulse(3, 700, 600) # wrist
    time.sleep(1.0)


def arm_left():
    Board.setPWMServoPulse(6, 2400, 600) # rotate
    
def arm_center():
    Board.setPWMServoPulse(6, 1500, 600) # rotate
    Board.setPWMServoPulse(3, 700, 300) # center wrist
    
def arm_right():
    Board.setPWMServoPulse(6, 600, 600) # rotate


def open_gripper():
    print("Opening.......")
    Board.setPWMServoPulse(1, 2000, 600)
    time.sleep(1.0)
    
def close_gripper():
    print("Closing.......")
    Board.setPWMServoPulse(1, 1500, 600)
    time.sleep(1.0)


def pick_up():
    open_gripper()
    arm_down()
    close_gripper()
    arm_up()
    
def roll_forward():
    print("Rolling forward.......")
    Board.setMotor(1, 50) #Left Front (Definitely having trouble with motors. Avoiding setting to 100 or -100)
    Board.setMotor(2, 50) #Right Front
    Board.setMotor(3, 50) #Left Rear
    Board.setMotor(4, 50) #Right Rear
    time.sleep(0.5)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)
                    
def roll_backward():
    print("Rolling backward.......")
    Board.setMotor(1, -50) #Left Front
    Board.setMotor(2, -50) #Right Front
    Board.setMotor(3, -50) #Left Rear
    Board.setMotor(4, -50) #Right Rear
    time.sleep(0.5)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)


def slide_left():
    print("Sliding left.......")
    Board.setMotor(1, -50) #Left Front
    Board.setMotor(2, 50) #Right Front
    Board.setMotor(3, 50) #Left Rear
    Board.setMotor(4, -50) #Right Rear
    time.sleep(0.5)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)
       
def slide_right():
    print("Sliding right.......")
    Board.setMotor(1, 50) #Left Front
    Board.setMotor(2, -50) #Right Front
    Board.setMotor(3, -50) #Left Rear
    Board.setMotor(4, 50) #Right Rearsu
    time.sleep(0.5)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)


def turn_left():
    print("Turning left.......")
    Board.setMotor(1, -50) #Left Front
    Board.setMotor(2, 50) #Right Front
    Board.setMotor(3, -50) #Left Rear
    Board.setMotor(4, 50) #Right Rear
    time.sleep(0.3)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)
    
def turn_right():
    print("Turning right.......")
    Board.setMotor(1, 50) #Left Front
    Board.setMotor(2, -50) #Right Front
    Board.setMotor(3, 50) #Left Rear
    Board.setMotor(4, -50) #Right Rear
    time.sleep(.3)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)
     
def stop_motors():
    print("Stopping motors.......")
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(1.0)


def play_edm():
    with subprocess.Popen(['mpg123', '-q', '-f', '12000', '/home/pi/MasterPi/HiwonderSDK/MP3s/2edm.mp3']) as process:
        time.sleep(18)
        process.terminate()
      
def play_bobby_caldwell():
    with subprocess.Popen(['mpg123', '-q', '-f', '29000', '/home/pi/MasterPi/HiwonderSDK/MP3s/2bobby-caldwell.mp3']) as process:
        time.sleep(18)
        process.terminate()     
  
def eyes_red():
    eyes.setPixelColor(0, Board.PixelColor(80, 0, 0))
    eyes.setPixelColor(1, Board.PixelColor(80, 0, 0))
    
def eyes_orange():
    eyes.setPixelColor(0, Board.PixelColor(80, 10, 0))
    eyes.setPixelColor(1, Board.PixelColor(80, 10, 0))
    
def eyes_yellow():
    eyes.setPixelColor(0, Board.PixelColor(80, 35, 0))
    eyes.setPixelColor(1, Board.PixelColor(80, 35, 0))
    
def eyes_green():
    eyes.setPixelColor(0, Board.PixelColor(0, 80, 0))
    eyes.setPixelColor(1, Board.PixelColor(0, 80, 0))
    
def eyes_blue():
    eyes.setPixelColor(0, Board.PixelColor(0, 0, 80))
    eyes.setPixelColor(1, Board.PixelColor(0, 0, 80))
    
def eyes_purple():
    eyes.setPixelColor(0, Board.PixelColor(40, 0, 80))
    eyes.setPixelColor(1, Board.PixelColor(40, 0, 80))
    
  
def pause_gpt():
    print("Pausing API calls. Say any command to restart...\n")
    global gpt_paused
    gpt_paused = True
      
def wake_up():
    global gpt_paused
    gpt_paused = False
    send_text_to_openai()
    execute_flares()


def exit_program():
    print("Exiting program")
    stop_motors()
    execute_flares()
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    eyes.setPixelColor(0, Board.PixelColor(0, 0, 0))
    eyes.setPixelColor(1, Board.PixelColor(0, 0, 0))
    cv2.destroyAllWindows()
    sys.exit()




################################################################################    


#3 - THESE ARE THE FUNCTIONS FOR FLOYD'S RANDOM "FLAIR" ACTIONS
def execute_flares():
    list_of_flares = [    
        flair_1, flair_2, flair_3, flair_4, flair_5, flair_6, 
        flair_7, flair_8, flair_9, flair_10, flair_11, flair_12,
        flair_13, flair_14, flair_15, flair_16, flair_17, flair_18,
        flair_19, flair_20
    ]  
    
    if random.random() < 1.00: # 100% chance to execute a first flair
        random.choice(list_of_flares)()
    if random.random() < 0.75: # 75% chance to execute a second flair
        random.choice(list_of_flares)()




def flair_1():
    print("  Trigger Flair One - Onboard Beep")
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0)) # Green LED
    Board.RGB.show()
    Board.setBuzzer(100)
    time.sleep(0.5)
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    Board.setBuzzer(0)


def flair_2():
    print("  Trigger Flair Two - Onboard Buzz")
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0)) # Red LED
    Board.RGB.show()
    for i in range(13):
        Board.setBuzzer(1)
        time.sleep(0.001)
        Board.setBuzzer(0)
        time.sleep(0.05)
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
   
def flair_3():
    print("  Trigger Flair Three - Onboard Chirp")
    Board.RGB.setPixelColor(0, Board.PixelColor(120, 120, 0)) # Yellow LED
    Board.RGB.show()   
    for i in range(13):
        Board.setBuzzer(1)
        time.sleep(0.015)
        Board.setBuzzer(0)
        time.sleep(0.015)    
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()


def flair_4():
    print("  Trigger Flair Four - Rotate arm to the right")
    Board.setPWMServoPulse(6, 900, 300)
    time.sleep(1.0)
    
def flair_5():
    print("  Trigger Flair Five - Rotate arm to center position")
    Board.setPWMServoPulse(6, 1500, 300)
    time.sleep(1.0)
    
def flair_6():
    print("  Trigger Flair Six - Rotate arm to the left")
    Board.setPWMServoPulse(6, 2100, 300)
    time.sleep(1.0)


def flair_7():
    print("  Trigger Flair Seven - Lower arm")
    Board.setPWMServoPulse(5, 950, 300)
    time.sleep(1.0)


def flair_8():
    print("  Trigger Flair Eight - Raise arm")
    Board.setPWMServoPulse(5, 800, 300)
    time.sleep(1.0)


def flair_9():
    print("  Trigger Flair Nine - Lower wrist")
    Board.setPWMServoPulse(3, 400, 300)
    
def flair_10():
    print("  Trigger Flair Ten - Center wrist")
    Board.setPWMServoPulse(3, 700, 300)


def flair_11():
    print("  Trigger Flair Eleven - Turn left")
    Board.setMotor(1, -50) #Left Front
    Board.setMotor(2, 50) #Right Front
    Board.setMotor(3, -50) #Left Rear
    Board.setMotor(4, 50) #Right Rear
    time.sleep(0.05)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    
def flair_12():
    print("  Trigger Flair Twelve - Turn right")
    Board.setMotor(1, 50) #Left Front
    Board.setMotor(2, -50) #Right Front
    Board.setMotor(3, 50) #Left Rear
    Board.setMotor(4, -50) #Right Rear
    time.sleep(0.05)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)  


def flair_13():
    print("  Trigger Flair Thirteen - Communication FX") # Playback volume varies from 0 to 32768
    Board.RGB.setPixelColor(0, Board.PixelColor(120, 120, 0)) # Yellow LED
    Board.RGB.show()   
    subprocess.run(['mpg123', '-q', '-f', '4000', '/home/pi/MasterPi/HiwonderSDK/MP3s/communication.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_14():
    print("  Trigger Flair Fourteen - Electro FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0)) # Red LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '6000', '/home/pi/MasterPi/HiwonderSDK/MP3s/electro.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_15():
    print("  Trigger Flair Fifteen - Low Boing FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(120, 255, 0)) # Orange LED ?
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '6000', '/home/pi/MasterPi/HiwonderSDK/MP3s/low-boing.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_16():
    print("  Trigger Flair Sixteen - R2 Chirp FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0)) # Green LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '9000', '/home/pi/MasterPi/HiwonderSDK/MP3s/R2-chirp.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_17():
    print("  Trigger Flair Seventeen - R2 Longer Squawk FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(120, 120, 0)) # Yellow LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '3000', '/home/pi/MasterPi/HiwonderSDK/MP3s/R2-longer-squawk.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_18():
    print("  Trigger Flair Eighteen - R2 Song FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0)) # Green LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '4000', '/home/pi/MasterPi/HiwonderSDK/MP3s/R2-song.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_19():
    print("  Trigger Flair Nineteen - R2 Splat FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0)) # Red LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '9000', '/home/pi/MasterPi/HiwonderSDK/MP3s/R2-splat.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()
    
def flair_20():
    print("  Trigger Flair Twenty - Static FX")
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0)) # Red LED
    Board.RGB.show()
    subprocess.run(['mpg123', '-q', '-f', '9000', '/home/pi/MasterPi/HiwonderSDK/MP3s/static.mp3'])
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.show()    
    
    
################################################################################


#4 - THIS FUNCTION RECORDS SPOKEN AUDIO AND SENDS IT TO OPENAI FOR TRANSCRIPTION
def record_audio_and_transcribe():
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    SILENCE_THRESHOLD = 650  # Adjust this threshold based on ambient noise, etc
    SILENCE_DURATION_TO_END = 1.2    # Seconds of silence before ending   


    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)
    frames = []
    last_sound_time = time.time()
    recording_started = False
    
    
    print("(1) Ready to parse audio. Please begin speaking...")
    while True: # Audio recording loop
        data = stream.read(CHUNK, exception_on_overflow=False)
            
        # This math calculates root mean square (RMS) to estimate sound volume
        rms_values = struct.unpack("<" + "h" * (len(data) // 2), data)
        rms = math.sqrt(sum(x**2 for x in rms_values) / len(rms_values)) 
        # print(f"RMS sound volume: {rms:.0f}")
         
        if rms >= SILENCE_THRESHOLD:
            recording_started = True  # Set flag to True           
            last_sound_time = time.time()    
            
        if recording_started:
            frames.append(data)
            if (time.time() - last_sound_time) > SILENCE_DURATION_TO_END:
                print("\n(2) 1.2 seconds of silence detected. End recording.")
                break
        
                   
    # Stop recording to clear resources
    stream.stop_stream()
    stream.close()


    # Write to a .wav file
    with wave.open("input-recording.wav", 'wb') as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(audio.get_sample_size(FORMAT))
        wav_file.setframerate(RATE)
        wav_file.writeframes(b''.join(frames))


    # API Call #1 - sends the .wav to OpenAI and receives a text transcription 
    print("\n(3) API Call #1 to transcribe the recorded audio into text...")
    with open("input-recording.wav", "rb") as audio_file:
        transcription = openai.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
        )
    
    # Error handler - The API tends to return these phrases when it can't parse
    if transcription.strip().lower().startswith(("thank you for watching", "thanks for watching", "you")):
        transcription = "No input received. Still waiting."
            
    print("(4) You said:")
    print("\033[95m   " + transcription + "\033[0m") # Prints transcription in magenta
    return transcription




################################################################################


#5 - THIS FUNCTION SENDS THE TEXT TRANSCRIPTION TO OPENAI AND PLAYS THE RESPONSE
def send_text_to_openai():
    global conversation_log
    
    # Add transcription to conversation log ("short term memory")
    conversation_log.append({"role": "user", "content": transcription})
    
    # Add camera image to conversation log
    base64_image = capture_image_and_encode()
#     if base64_image is None:
#         print("(5) Failed to capture image......")
#         return
    image_message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "Current camera view:"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }
    
    conversation_log.append(image_message)
  
    # API Call #2 - sends the appended conversation log and receives a response
    print("(6) API Call #2 to produce a text response from GPT...")
    response = openai.chat.completions.create(
        model = "gpt-4o",
        messages=conversation_log
    )  
    text_response = response.choices[0].message.content
    
    
    # If the text_response is long we start playing some "on-hold" audio
    mp3_playing = False
    if len(text_response) > 60:
        mp3_playing = True
        on_hold_mp3s = [
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1computer-processing.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1data-sound.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1data-transmission01.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1data-transmission02.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1eight-bit-beeping.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1girl-from-ipanema.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1glitch-madness.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1heavenly-computer.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1pacman-variations.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1retro-computer.mp3",
            "/home/pi/MasterPi/HiwonderSDK/MP3s/1robot-speech.mp3"
        ]
        random_choice = random.choice(on_hold_mp3s)
        on_hold_audio = subprocess.Popen(["mpg123", "-q", "-f", "2600", random_choice])
        print("\n(7) Playing an on-hold mp3: " + random_choice + "...") 
    
    print('\n(8) GPT response received:')
    print('\033[95m   ' + text_response + '\033[0m') # Prints response in magenta
 


    # Prune conversation_log - remove older messages, but retains "personality"   
    conversation_log.pop()  # Removes the recent image
    if len(conversation_log) > 150:
        conversation_log = [conversation_log[0]] + conversation_log[-149:]
        
    conversation_log.append({"role": "assistant", "content": text_response})
  
         
    # API Call #3 - convert the text response into a speech audio file
    print("\n(9) API Call #3 to convert the text response into speech (mp3)...")
    audio_response = openai.audio.speech.create(   
        model="tts-1",
        voice=TTS_voice,
        speed=TTS_speed,
        input=text_response,
    )


    # Stop playing the "on-hold" audio (if playing)
    if mp3_playing:
        on_hold_audio.terminate()
        on_hold_audio.wait()
        mp3_playing = False
    
    
    # Here we open an mp3 audio file and write to it (streaming will be better)
    with open("speech-response.mp3", "wb") as f:
        f.write(audio_response.content)
        
  
    # Use subprocess mpg123 to play the audio file
    print("(10) Now playing the audio response...\n")
    subprocess.run(["mpg123", "-q", "-f", "32768", "speech-response.mp3"])
    
    print(f"Number of elements now in the conversation_log = {len(conversation_log)}")




################################################################################


#6 - THIS DICTIONARY LISTS ALL THE POSSIBLE VOICE COMMANDS FLOYD RECOGNIZES
voice_commands = {
    "test servos": test_servos,
    "arm down": arm_down,
    "arm up": arm_up,
    "arm left": arm_left,
    "arm center": arm_center,
    "arm right": arm_right,
    "open": open_gripper,
    "drop": open_gripper,
    "close": close_gripper,
    "pickup": pick_up,
    "pick up": pick_up,
    
    "roll forward": roll_forward,
    "move forward": roll_forward,
    "roll forwards": roll_forward,
    "move forwards": roll_forward,
    "roll backward": roll_backward,
    "move backward": roll_backward,
    "roll backwards": roll_backward,
    "move backwards": roll_backward,
    
    "slide left": slide_left,
    "move left": slide_left,
    "slide right": slide_right,
    "move right": slide_right,
    "turn left": turn_left,
    "turn right": turn_right,
    
    "let's dance": play_edm,
    "music": play_bobby_caldwell,
    
    "eyes red": eyes_red,
    "eyes orange": eyes_orange,
    "eyes yellow": eyes_yellow,
    "eyes green": eyes_green,
    "eyes blue": eyes_blue,
    "eyes purple": eyes_purple,
    
    "anger": eyes_red,
    "anxiety": eyes_orange,
    "happiness": eyes_yellow,
    "disgust": eyes_green,
    "sadness": eyes_blue,
    "fear": eyes_purple,
    
    "pause": pause_gpt,
    "wake up": wake_up,
    "exit": exit_program,
    "that's it": exit_program,
    }




################################################################################


#7 - HERE'S THE MAIN ROUTINE - WHICH IS BASICALLY JUST AN ENDLESS LOOP
heartbeat = threading.Thread(target=flash_LED, daemon=True)
heartbeat.start()


video_thread = threading.Thread(target=display_video_feed, daemon=True)
video_thread.start()




while True: 
    print("\n\n*** EXECUTING MAIN ROUTINE *** ")
#    stop_motors() # Used for debugging motor function
    transcription = record_audio_and_transcribe()


    transcription_lowercase = transcription.lower().strip()
    for trigger, action in voice_commands.items():
#        if trigger in transcription_lowercase:
        if transcription_lowercase.startswith(trigger):
            gpt_paused = False # Any command will wake up the GPT calls
            action()
            break     
    else:
        if gpt_paused:
            print("Zzzz. API calls are currently paused. Listening for any command...\n")
        else:
            send_text_to_openai()
            execute_flares()