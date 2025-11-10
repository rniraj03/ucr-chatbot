import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

class LLMClient:
    """Interface for Gemini LLM interactions"""
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash")
        self.chat = None

    def start_chat(
        self,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict]] = None,
    ) -> None:
        """Initialize chat session with optional system prompt and history"""
        if system_prompt:
            self.model = genai.GenerativeModel(
                "models/gemini-2.0-flash",
                system_instruction=system_prompt,
            )

        gemini_history = []
        if history:
            for msg in history:
                # Convert to proper Gemini format
                if "parts" in msg:
                    gemini_history.append(msg)
                else:
                    gemini_history.append({
                        "role": msg.get("role", "user"),
                        "parts": [{"text": msg.get("content", "")}]
                    })

        self.chat = self.model.start_chat(history=gemini_history)

    def send_message(self, message: str) -> str:
        """Send a message and return full response"""
        if not self.chat:
            self.start_chat()

        response = self.chat.send_message(message)
        return response.text

    def send_message_stream(self, message: str):
        """Stream Gemini’s response"""
        if not self.chat:
            self.start_chat()

        try:
            response = self.chat.send_message(message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"[ERROR] Gemini stream failed: {e}")
            yield "(Error: Gemini API call failed.)"

    def get_history(self) -> List[Dict]:
        """Return chat history"""
        if not self.chat:
            return []

        history = []
        for msg in self.chat.history:
            history.append({
                "role": msg.role,
                "content": msg.parts[0].text
            })
        return history
