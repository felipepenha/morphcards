import os
import sys
from dotenv import load_dotenv

# Attempt to import OpenAI and Google Generative AI libraries
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

def check_openai_connectivity(api_key: str) -> bool:
    if not openai:
        print("OpenAI library not installed. Skipping OpenAI connectivity check.")
        return False
    try:
        client = openai.OpenAI(api_key=api_key)
        # Attempt to list models as a simple connectivity test
        client.models.list()
        print("✅ OpenAI API connection successful!")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

def check_gemini_connectivity(api_key: str) -> bool:
    if not genai:
        print("Google Generative AI library not installed. Skipping Gemini connectivity check.")
        return False
    try:
        genai.configure(api_key=api_key)
        # Attempt a simple model listing or a dummy generation
        genai.list_models()
        print("✅ Gemini API connection successful!")
        return True
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

def main():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    print("--- Checking API Connectivity ---")

    openai_success = False
    gemini_success = False

    if openai_api_key:
        print("\nAttempting OpenAI API connection...")
        openai_success = check_openai_connectivity(openai_api_key)
    else:
        print("\nSkipping OpenAI API check: OPENAI_API_KEY not found in .env")

    if gemini_api_key:
        print("\nAttempting Gemini API connection...")
        gemini_success = check_gemini_connectivity(gemini_api_key)
    else:
        print("\nSkipping Gemini API check: GEMINI_API_KEY not found in .env")

    print("\n--- Connectivity Check Complete ---")

    if not (openai_success or gemini_success):
        print("Neither OpenAI nor Gemini API could be connected successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()
