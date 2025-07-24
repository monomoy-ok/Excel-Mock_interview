from gtts import gTTS
import pygame
import tempfile

text = "नमस्ते, यह एक परीक्षण है।"
fp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
tts = gTTS(text=text, lang='hi')
tts.save(fp.name)
fp.close()
pygame.mixer.init()
pygame.mixer.music.load(fp.name)
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    continue
pygame.mixer.quit()