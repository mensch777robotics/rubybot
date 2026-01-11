from google.cloud import texttospeech
from dotenv import load_dotenv
import os
import pygame


load_dotenv()
pygame.init()

class RubyTTS:
    """
    Ruby Text-to-Speech (TTS) Module.

    This class handles converting text responses into spoken audio using the Google Cloud Text-to-Speech API.
    It supports multiple languages (English, Malayalam, Tamil) and manages audio playback using `pygame`.
    
    Attributes:
        language_config (dict): Configuration for supported languages including voice name and gender.
        client (TextToSpeechClient): Google Cloud TTS client.
        cache_dir (str): Directory to temporarily store generated audio files.
        sample_rate_hertz (int): Audio sample rate for playback (default: 24000).
    """
    def __init__(self,
    language="en-IN",
    audio_encoding=texttospeech.AudioEncoding.MP3,
    sample_rate_hertz=24000,
    cache_dir=".cache",
    speaking_rate=None
    ):
        """
        Initialize the RubyTTS instance.

        Args:
            language (str): Default language code (e.g., 'en-IN').
            audio_encoding (AudioEncoding): Audio format (default: MP3).
            sample_rate_hertz (int): Audio sample rate (default: 24000).
            cache_dir (str): Path to store temporary audio files (default: '.cache').
            speaking_rate (float, optional): Speed of speech (0.25 to 4.0). Overrides language defaults if set.
        """
        # Configuration for supported languages (Indian Context)
        self.language_config = {
            'en-IN': {
                'voice_name': 'en-IN-Standard-D',  # Preferred English voice
                'gender': texttospeech.SsmlVoiceGender.FEMALE,
                'speaking_rate': 0.75
            },
            'ml-IN': {
                'voice_name': 'ml-IN-Standard-A',  # Preferred Malayalam voice
                'gender': texttospeech.SsmlVoiceGender.FEMALE,
                'speaking_rate': 0.75
            },
            'ta-IN': {
                'voice_name': 'ta-IN-Standard-A',  # Preferred Tamil voice
                'gender': texttospeech.SsmlVoiceGender.FEMALE,
                'speaking_rate': 0.75
            }
        }
        
        # Initialize Google Cloud Client and Audio Settings
        self.client = texttospeech.TextToSpeechClient() 
        self.language_code = language 
        self.audio_encoding = audio_encoding 
        self.cache_dir = cache_dir 
        self.sample_rate_hertz = sample_rate_hertz 
        
        # Determine speaking rate: use argument if provided, else fall back to language default
        if speaking_rate is not None:
            self.speaking_rate = speaking_rate
        else:
            self.speaking_rate = self.language_config[language]['speaking_rate']
            
        os.makedirs(self.cache_dir, exist_ok=True) # Ensure cache directory exists

        # Configure Voice Params (Language, Name, Gender)
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.language_config[language]['voice_name'],
            ssml_gender=self.language_config[language]['gender'],
        )
        
        # Configure Audio Params (Encoding, Sample Rate, Speed)
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=self.audio_encoding,
            sample_rate_hertz=self.sample_rate_hertz,
            speaking_rate=self.speaking_rate,
        )
    
    def update_language(self, language, speaking_rate=None):
        """
        Switch the TTS language dynamically.

        Updates the internal configuration to generate speech in a new language.
        If the language is not supported, it defaults to English (en-IN).

        Args:
            language (str): The target BCP-47 language code.
            speaking_rate (float, optional): New speaking rate for this language.
        """
        print(f"Updating to {language}")
        if language not in self.language_config:
            print(f"Language {language} not supported. Using default language: en-IN")
            language = 'en-IN'
            
        self.language_code = language
        
        # Update speaking rate and refresh configs
        if speaking_rate is not None:
            self.speaking_rate = speaking_rate
        else:
            self.speaking_rate = self.language_config[language]['speaking_rate']
            
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.language_config[language]['voice_name'],
            ssml_gender=self.language_config[language]['gender'],
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=self.audio_encoding,
            sample_rate_hertz=self.sample_rate_hertz,
            speaking_rate=self.speaking_rate,
        )
    
    def update_speaking_rate(self, speaking_rate):
        """
        Adjust the speed of speech without changing language.

        Args:
            speaking_rate (float): New speaking rate (0.25 to 4.0).
        """
        self.speaking_rate = speaking_rate
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=self.audio_encoding,
            sample_rate_hertz=self.sample_rate_hertz,
            speaking_rate=self.speaking_rate,
        )
    
    def get_current_language(self):
        """Returns the currently active BCP-47 language code."""
        return self.language_code
    
    def get_supported_languages(self):
        """Returns a list of all supported language codes."""
        return list(self.language_config.keys())

    def text_to_speech(self, text):
        """
        Synthesize text to speech and play it immediately.

        1. Validates input text.
        2. Sends request to Google Cloud TTS API.
        3. Saves the audio content to a temporary cache file.
        4. Plays the audio using Pygame mixer.
        5. Deletes the cache file after playback.

        Args:
            text (str): The text message to speak.
        """
        if not text or not isinstance(text, str):
            print("No text provided for synthesis.")
            return None
        
        input_text = texttospeech.SynthesisInput(text=text)
        
        # Request speech synthesis
        response = self.client.synthesize_speech(
            input=input_text,
            voice=self.voice,
            audio_config=self.audio_config,
        )
        
        # Save audio stream to a temporary cache file
        # Using first 5 chars of text in filename to avoid filesystem issues with long names
        safe_text_snippet = "".join(x for x in text[:5] if x.isalnum())
        cache_file = os.path.join(self.cache_dir, f"{self.language_code}_{safe_text_snippet}.mp3")
        
        with open(cache_file, "wb") as out:
            out.write(response.audio_content)
        
        # Load and play the audio file
        pygame.mixer.music.load(cache_file)
        pygame.mixer.music.play()
        
        # Block until playback finishes (simple loop with Clock tick)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Cleanup: Remove the temporary file
        try:
            os.remove(cache_file)
        except OSError:
            pass # Ignore if file is already gone or locked

    def stop(self):
        """Immediately stop any currently playing audio."""
        pygame.mixer.music.stop()


            