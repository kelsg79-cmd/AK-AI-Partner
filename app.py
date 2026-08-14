import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

HUKOMMELSESFIL = "memory.json"


def hent_hukommelse():
    if os.path.exists(HUKOMMELSESFIL):
        with open(HUKOMMELSESFIL, "r", encoding="utf-8") as fil:
            return json.load(fil)
    return []


def gem_hukommelse(samtale):
    with open(HUKOMMELSESFIL, "w", encoding="utf-8") as fil:
        json.dump(samtale, fil, ensure_ascii=False, indent=2)


samtale = hent_hukommelse()

print("AK-AI-Partner er startet.")
print("Skriv 'stop' for at afslutte.\n")

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
            "Du hjælper brugeren klart, praktisk og på dansk. "
            "Brug den tidligere samtale som hukommelse."
        ),
        input=samtale,
    )

    svar = response.output_text

    samtale.append({
        "role": "assistant",
        "content": svar
    })

    gem_hukommelse(samtale)

    print(f"\nAK-AI-Partner: {svar}\n")