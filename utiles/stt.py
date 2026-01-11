import os
import sounddevice as sd 
from google.cloud import speech
from dotenv import load_dotenv

load_dotenv()

class RubySTT:
    """
    Ruby Speech-to-Text (STT) Module.

    This class handles real-time speech recognition using the Google Cloud Speech-to-Text API.
    It captures audio from the system's microphone using `sounddevice` and streams it to Google's
    services for transcription.
    """
    def __init__(
        self,
        language_code: str = "en-IN",
        sample_rate: int = 16_000,
        chunk: int = 100,
        phrases: list[str] = None,
        phrases_boost: int = 20,
    ):
        """
        Initialize the RubySTT instance.

        Args:
            language_code (str): The language code for recognition (default: 'en-IN').
            sample_rate (int): The sample rate for audio capture (default: 16_000).
            chunk (int): Audio chunk size for processing (default: 100).
            phrases (list[str]): Context phrases to improve recognition of specific words.
            phrases_boost (int): Boost value for the context phrases (default: 20).
        """
        self.phrases = phrases
        self.language_code = language_code
        self.sample_rate = sample_rate
        self.chunk_size = chunk
        
        # Configure SpeechContext to boost recognition of specific phrases (e.g., "Ruby")
        self.speech_contexts = ([speech.SpeechContext(phrases=phrases,boost=phrases_boost)]if phrases else None)
        
        # Define the recognition configuration for Google Cloud
        self.recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
            speech_contexts=self.speech_contexts,
        )
        
        # Define the streaming configuration
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.recognition_config,
            single_utterance=False, # Keep connection open for continuous conversation
            interim_results=True,   # Receive intermediate results for lower latency feeling
        )
        
        # Initialize the Google Cloud Speech Client
        self.client = speech.SpeechClient()
    
    def update_language(self, language_code: str):
        """
        Update the recognition language dynamically.

        This allows the agent to switch between languages (e.g., English to Malayalam) 
        without restarting the application. The client is re-initialized with new configs.

        Args:
            language_code (str): The new BCP-47 language code.
        """
        self.language_code = language_code
        self.recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
            speech_contexts=self.speech_contexts,
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.recognition_config,
            single_utterance=False,
            interim_results=True,
        )
        self.client = speech.SpeechClient()
    
    def _audio_stream(self):
        """
        Generator that yields audio chunks from the microphone.

        Uses the `sounddevice` library to create an input stream.
        This runs in an infinite loop reading data until the stream is closed.
        
        Yields:
             bytes: Raw audio data in bytes.
        """
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.chunk_size,
        ) as stream:
            while True:
                data, _ = stream.read(self.chunk_size)
                yield data.tobytes()
        
    def listen(self) -> str:
        """
        Accurately listen to user input and return the transcribed text.

        1. Starts the microphone stream.
        2. Sends requests to Google Cloud Speech API.
        3. Iterates through responses to find the 'final' result.

        Returns:
            str: The final transcribed text from the user.
        """
        print("Listening...")
        # Create a generator of requests containing audio chunks
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in self._audio_stream()
        )

        # Send the streaming request to Google Cloud
        responses = self.client.streaming_recognize(
            config=self.streaming_config,
            requests=requests,
        )

        # Process the stream of responses
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            # 'is_final' indicates that the API has finished processing this utterance
            if result.is_final:
                return result.alternatives[0].transcript

        return ""
    
