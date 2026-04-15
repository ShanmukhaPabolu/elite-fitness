import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
print(f"API Key found: {api_key is not None}")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Try both models
        for model_name in ['gemini-1.5-flash', 'gemini-2.0-flash']:
            print(f"Testing model: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hi, are you working?")
                print(f"SUCCESS ({model_name}): {response.text}")
                break
            except Exception as e:
                print(f"ERROR ({model_name}): {str(e)}")
    except Exception as e:
        print(f"GLOBAL ERROR: {str(e)}")
else:
    print("NO API KEY FOUND")
