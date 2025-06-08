from openai import OpenAI

openai_api_key = "YOUR_OPENAI_API_KEY"
client = OpenAI(api_key=openai_api_key)

def chat_with_model(prompt):
    """Chatbot response using OpenAI GPT."""
    try:
        response = client.completions.create(
            model="gpt-4o",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"