from langchain_core.tools import tool
import serial
import time
from utiles import rag_utiles

@tool
def calculator(query: str) -> str:
    """Evaluates a basic mathematical expression provided as a string. 
    Supports arithmetic operations like addition, subtraction, multiplication, division, and parentheses."""
    try:
        return str(eval(query))
    except Exception as e:
        return str(e)

@tool
def arduino_serial_communication(query: str) -> str:
    """Communicates with an Arduino device via serial connection."""
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600)
        time.sleep(2)
        ser.write(query.encode())
        return "Arduino Serial Communication Successful"
    except Exception as e:
        return str(e)

@tool
def query_document(query: str) -> str:
    """Queries a document using the RobiRAG class."""
    try:
        return rag_utiles.RobiRAG().query(query)
    except Exception as e:
        return str(e)