import os
import openai
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3")

# ── OpenAI Client ─────────────────────────────────────────────────────────────
client = openai.OpenAI(api_key=OPENAI_API_KEY)   # ← fixed


def call_openai(prompt: str) -> str:
    """Call OpenAI GPT-4o-mini and return raw text response."""
    response = client.chat.completions.create(
        model       = "gpt-4.1",
        messages    = [
            {
                "role":    "system",
                "content": "You are an expert fitness coach with 30+ years experience. "
                           "Always respond in valid JSON only. No markdown. No extra text."
            },
            {
                "role":    "user",
                "content": prompt
            }
        ],
        temperature = 0.2,     # ← variety in responses
        max_tokens  = 6000     # ← enough for full weekly plan
    )
    return response.choices[0].message.content


def call_gemini(prompt: str) -> str:
    """Call Gemini and return raw text response."""
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")

    genai.configure(api_key=GEMINI_API_KEY)
    model    = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def call_llm_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Priority:
    1. OpenAI  → best quality
    2. Gemini  → free tier backup
    3. Raises  → fallback plan used
    """

    # Try OpenAI first
    try:
        print("Trying OpenAI...")
        result = call_openai(prompt)
        return result, "openai"
    except Exception as e:
        print(f"OpenAI failed: {e} — trying Gemini...")

    # Try Gemini
    try:
        print("Trying Gemini...")
        result = call_gemini(prompt)
        return result, "gemini"
    except Exception as e:
        print(f"Gemini also failed: {e}")
        raise Exception("All AI providers failed")

# ##OLLAMA INTEGRATION
# import os
# import openai
# import google.generativeai as genai
# import ollama as ollama_client
# from dotenv import load_dotenv

# load_dotenv()

# openai.api_key = os.getenv("OPENAI_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3")


# def call_openai(prompt: str) -> str:
#     response = openai.chat.completions.create(
#         model    = "gpt-4o-mini",
#         messages = [
#             {"role": "system", "content": "You are an expert fitness coach. Always respond in valid JSON only."},
#             {"role": "user",   "content": prompt}
#         ],
#         temperature = 0.3,
#         max_tokens  = 6000
#     )
#     return response.choices[0].message.content


# def call_gemini(prompt: str) -> str:
#     genai.configure(api_key=GEMINI_API_KEY)
#     model    = genai.GenerativeModel("gemini-1.5-flash")
#     response = model.generate_content(prompt)
#     return response.text


# def call_ollama(prompt: str) -> str:
#     """Call local Ollama model — completely free."""
#     response = ollama_client.chat(
#         model    = OLLAMA_MODEL,
#         messages = [
#             {
#                 "role":    "system",
#                 "content": "You are an expert fitness coach. Always respond in valid JSON only. No markdown, no extra text."
#             },
#             {
#                 "role":    "user",
#                 "content": prompt
#             }
#         ]
#     )
#     return response["message"]["content"]


# def call_llm_with_fallback(prompt: str) -> tuple[str, str]:
#     """
#     Priority order:
#     1. Ollama (local — free)
#     2. OpenAI (cloud — paid)
#     3. Gemini (cloud — free tier)
#     4. Fallback plan
#     """

#     # Try Ollama first — free and local
#     try:
#         print("Trying Ollama (local)...")
#         result = call_ollama(prompt)
#         return result, "ollama"
#     except Exception as e:
#         print(f"Ollama failed: {e} — trying OpenAI...")

#     # Try OpenAI
#     try:
#         print("Trying OpenAI...")
#         result = call_openai(prompt)
#         return result, "openai"
#     except Exception as e:
#         print(f"OpenAI failed: {e} — trying Gemini...")

#     # Try Gemini
#     try:
#         print("Trying Gemini...")
#         result = call_gemini(prompt)
#         return result, "gemini"
#     except Exception as e:
#         print(f"Gemini also failed: {e}")
#         raise Exception("All AI providers failed")