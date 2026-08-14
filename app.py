from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

print("AK-AI-Partner er startet.")
print("Skriv 'stop' for at afslutte.\n")

samtale = []

while True:
    besked = input("Dig: ")

    if besked.lower() == "stop":
        print("AK-AI-Partner: Vi ses!")
        break

    samtale.append({
        "role": "user",
        "content": besked
    })

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "Du er AK-AI-Partner. "
            "Du hjælper brugeren klart, praktisk og på dansk."
        ),
        input=samtale,
    )

    svar = response.output_text

    samtale.append({
        "role": "assistant",
        "content": svar
    })

    print(f"\nAK-AI-Partner: {svar}\n")