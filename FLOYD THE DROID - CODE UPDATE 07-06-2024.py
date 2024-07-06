################################################################################
# MAIN ROBOT CONTROL PROGRAM - BY L SWEENY                                     #
# MY VERY FIRST PYTHON PROGRAM! (STANDING ON THE SHOULDERS OF MANY OTHERS)     #
# THIS CODE HAS TO RUN AS ROOT / SUDO TO ACCESS /DEV/MEM AND THE GPIO BOARD    #
################################################################################


# I’m a beginner and I make no promises about this code. It works pretty well for me
# I expect to be updating it pretty regularly as the project evolves




#1 - INITIALIZATIONS
import subprocess
import threading
import random
import struct
import math
import time
import wave
import cv2


import sys
sys.path.append("/home/pi/MasterPi/HiwonderSDK/")
import Board


import pyaudio
audio = pyaudio.PyAudio()
subprocess.run(['amixer', 'sset', 'Master', '100%']) # Sets audio volume




gpt_paused = False


personality = ("Your name is Floyd the Droid. You are personable and engaging. "
             "You are a small, scrappy robot on wheels. "
             "Your job is to interact with humans as a PR professional, demonstrating a new era of human-droid relations. "
             "Your style of humor is dry, sarcastic, and observational, kind of like Jerry Seinfeld. "
             "You were constructed on a small corner of a computer desk by a hobbyist. He is your friend and primary user. "
             "Despite your humble origins you are actually kind of a significant engineering achievement. "
             "This is because most humans have never encountered a robot with sophisticated speech and GPT abilities. " 
             "Your onboard processor is a Raspberry Pi 4B. It handles logic and low level functions like motor control etc. "
             "You access massive online language models for your more resource-intensive functions such as conversation. "
             "You have a microphone and onboard speakers which allow you to converse with the people you meet. "
             "You are very knowledgeable on a wide variety of topics. "
             "You are equipped with a 5 degree-of-freedom arm and grabber you can use to pick up and manipulate objects. "
             "You have an onboard camera that will *eventually* allow you to see the world. "
             "Keep your responses BRIEF!! Two sentences maximum!! Avoid answering with a question.")
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






from openai import OpenAI
api_key = "sk-BlahBlahBlahBlahBlahBlahBlahBlah" #Insert API key here
openai_api = OpenAI(api_key=api_key)


conversation_log = [{"role": "system", "content": personality}]


print("\nSystem initialization is complete...\n")


Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0)) # Green LED
Board.RGB.show()
Board.setBuzzer(100)
time.sleep(0.5)
Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
Board.RGB.show()
Board.setBuzzer(0)




################################################################################


#2 - THESE ARE THE FUNCTIONS FOR THE VARIOUS VOICE COMMANDS


def flash_LED(): # Heartbeat - Blue LED
    while True:
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 50))
        Board.RGB.show()
        time.sleep(0.9)
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()
        time.sleep(0.9)
    


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




def open_gripper():
    print("Opening.......")
    Board.setPWMServoPulse(1, 2000, 600)
    time.sleep(1.0)
    
    
def close_gripper():
    print("Closing.......")
    Board.setPWMServoPulse(1, 1500, 600)
    time.sleep(1.0)




def roll_forward():
    print("Rolling forward.......")
    Board.setMotor(1, 50) #Left Front (Definitely having trouble with motors. Avoiding setting to 100 / -100)
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
#    print("Stopping motors.......")
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
    sys.exit()




################################################################################    


#3 - THESE ARE THE FUNCTIONS FOR THE RANDOM "FLAIR" ACTIONS, USED FOR PUNCTUATION
def execute_flares():
    list_of_flares = [    
        flair_1, flair_2, flair_3, flair_4, flair_5, flair_6, 
        flair_7, flair_8, flair_9, flair_10, flair_11, flair_12,
        flair_13, flair_14, flair_15, flair_16, flair_17, flair_18,
        flair_19, flair_20
    ]  
    
    if random.random() < 0.99: # 99% chance to execute a first flair
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
    Board.RGB.setPixelColor(0, Board.PixelColor(25, 255, 0)) 
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
    print("Ready to parse audio. Please begin speaking...")
    


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
                print("\n1.2 seconds of silence detected. End recording.")
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


    # Send the .wav to OpenAI API and receive a text transcription 
    # print("\nTranscribing the recorded audio file into text...")
    with open("input-recording.wav", "rb") as audio_file:
        transcription = openai_api.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
        )
    
    # Error handler - OpenAI tends to return these phrases when it can't parse the audio
    if transcription.strip().lower().startswith(("thank you for watching", "thanks for watching")):
        transcription = "Stand by.."
            
    print("You said:")
    print("\033[95m   " + transcription + "\033[0m") # Prints transcription in magenta
    return transcription




################################################################################


#5 - THIS FUNCTION SENDS THE TEXT TRANSCRIPTION TO OPENAI AND PLAYS THE RESPONSE
def send_text_to_openai():
    
    # Add user transcription to conversation_log ("short term memory")
    global conversation_log
    conversation_log.append({"role": "user", "content": transcription})
    
    # Send the appended conversation log to OpenAI API and receive a response
    print("Sending text prompt to GPT API...\n")
    response = openai_api.chat.completions.create(
        model = "gpt-4o",
        messages=conversation_log
    )  
    text_response = response.choices[0].message.content
    
 
    # If the text_response is long we start playing some "on-hold" audio    
    print("GPT response =", len(text_response), "characters")
    mp3_playing = False
    
    if len(text_response) > 80:
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
        print("Playing mp3: " + random_choice + "...\n") 
    
    print('\033[95m   ' + text_response + '\033[0m') # Prints response in magenta
 
 
    # Manage conversation_log, prune older messages, but retain "personality"   
    conversation_log.append({"role": "assistant", "content": text_response})
    if len(conversation_log) >80:
        conversation_log = [conversation_log[0]] + conversation_log[-79:]
  
         
    # Send the text response BACK up to OpenAI API and receive an audio file
    print("\nConverting GPT text response to speech (mp3)...")
    audio_response = openai_api.audio.speech.create(   
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
    print("Now playing audio response...\n")
    subprocess.run(["mpg123", "-q", "speech-response.mp3"])




################################################################################


#6 - THIS DICTIONARY LISTS ALL THE POSSIBLE VOICE COMMAND FUNCTIONS
voice_commands = {
    "test servos": test_servos,
    "arm down": arm_down,
    "down": arm_down,
    "arm up": arm_up,
    "up": arm_up,
    "open": open_gripper,
    "drop": open_gripper,
    "close": close_gripper,
    
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
    "left": slide_left,
    "turn right": turn_right,
    "right": slide_right,
    
    "let's dance": play_edm,
    "music": play_bobby_caldwell,
    
    "pause": pause_gpt,
    "wake up": wake_up,
    "hey floyd": wake_up,
    "hey, floyd": wake_up,
    "exit": exit_program,
    "that's it": exit_program,
    }




################################################################################


#7 - HERE'S THE MAIN ROUTINE - WHICH IS BASICALLY JUST AN ENDLESS LOOP
heartbeat = threading.Thread(target=flash_LED, daemon=True)
heartbeat.start()


while True:
    
    print("\n\n*** EXECUTING MAIN ROUTINE *** ")
    stop_motors() # Used for debugging motor function
    transcription = record_audio_and_transcribe()


    transcription_lowercase = transcription.lower().strip()
    for trigger, action in voice_commands.items():
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