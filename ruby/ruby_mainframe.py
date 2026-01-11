from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import sys
import os

# Ensure utils can be imported by adding parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utiles.tts import RubyTTS
from utiles.stt import RubySTT
from utiles.prompt import system_prompt
from utiles.ruby_tools import (
    YouTubeVideoPlayerTool,
    GetAvailableLanguagesTool,
    SwitchLanguageTool,
)
from utiles.toolbox import (
    calculator,
    query_document,
    arduino_serial_communication,
)
load_dotenv()


class Ruby:
    """
    Ruby Mainframe Class.

    This class serves as the central brain of the Ruby assistant. 
    It integrates Speech-to-Text (STT), Text-to-Speech (TTS), and the LangChain 
    agent logic to handle user interactions and tool execution.
    """
    def __init__(self, tts=None, model="gpt-4o", system_prompt=system_prompt, tools=[], stt=None):
        """
        Initialize the Ruby agent.

        Args:
            tts: RubyTTS instance (optional).
            model: Name of the OpenAI model to use (default: "gpt-4o").
            system_prompt: System instructions for the agent.
            tools: List of additional tools.
            stt: RubySTT instance (optional).
        """
        self.model_name = model
        self.ruby_state = "idel"
        self.system_prompt = system_prompt
        
        # Combine default built-in tools with any extra tools provided
        self.tools = [
                        YouTubeVideoPlayerTool(self),   # Tool for playing YouTube videos
                        GetAvailableLanguagesTool(self), # Tool to check supported languages
                        SwitchLanguageTool(self),       # Tool to switch active language
                        calculator,                     # Basic calculator
                        query_document,                 # RAG document query tool
                        arduino_serial_communication,   # Hardware control tool
                    ] + tools

        # Initialize TTS (Text-to-Speech)
        if tts is None:
            self.tts = RubyTTS()
        else:
            self.tts = tts
            
        # Initialize STT (Speech-to-Text)
        if stt is None:
            self.stt = RubySTT()
        else:
            self.stt = stt

        self.system_prompt = system_prompt
        # Initialize conversation history with the system prompt
        self.chat_history = {"messages": [SystemMessage(content=self.system_prompt)]}
        
        # Create the LangChain agent
        self.model = create_agent(
            model=ChatOpenAI(model_name=self.model_name),
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def speak(self, user_input):
        """
        Process user input and generate a response.
        
        1. Updates state to 'Thinking'.
        2. Appends user input to history.
        3. Invokes model to get response.
        4. Updates state to 'Speaking' and plays audio.
        5. Returns text response.
        """
        self.ruby_state = "Thinking"
        self.chat_history["messages"].append(HumanMessage(content=user_input))
        
        # Get response from the agent
        response = self.model.invoke(self.chat_history)
        
        # Add agent's response to history
        self.chat_history["messages"].append(response["messages"][-1])
        
        self.ruby_state = "Speaking"
        # Synthesis speech from the text response
        self.tts.text_to_speech(response["messages"][-1].content)
        
        self.ruby_state = "idel"
        return response["messages"][-1].content
    
    def listen(self):
        """
        Listen for user audio input.
        
        Updates state to 'Listening' and activates the STT engine.
        """
        self.ruby_state = "Listening"
        transcript = self.stt.listen()
        print(f"User: {transcript}")
        return transcript

    def reset(self):
        """Reset the conversation history to the initial system prompt."""
        self.chat_history = {"messages": [SystemMessage(content=self.system_prompt)]}
        self.ruby_state = "idel"

    def run(self):
        """
        Main loop for console-based interaction.
        Continuously listens and speaks.
        """
        while True:
            user_input = self.listen()
            self.speak(user_input)
