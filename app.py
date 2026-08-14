import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

HUKOMMELSESFIL = "memory.json"
FAKTAFIL = "facts.json"


def hent_json(filnavn, standard):
    if os.path.exists(filnavn):
        with open(filnavn, "r", encoding="utf-8") as fil:
            return json.load(fil)
    return standard


def gem_json(filnavn, data):
    with open(filnavn, "w", encoding="utf-8") as fil:
        json.dump(data, fil, ensure_ascii=False, indent=2)


samtale = hent_json(HUKOMMELSESFIL, [])
fakta = hent_json(FAKTAFIL, [])

print("AK-AI-Partner er startet.")
print("Skriv 'stop' for at afslutte.")
print("Skriv 'husk: ...' for at gemme noget i langtidshukommelsen.\n")

while True:
    besked = input("Dig: ")

    if besked.lower() == "stop":
        print("AK-AI-Partner: Vi ses!")
        break

    if besked.lower().startswith("husk:"):
        ny_fakta = besked[5:].strip()

        if ny_fakta:
            fakta.append(ny_fakta)
            gem_json(FAKTAFIL, fakta)
            print(f"AK-AI-Partner: Det husker jeg: {ny_fakta}\n")
        continue

    kendte_fakta = "\n".join(f"- {faktum}" for faktum in fakta)

    samtale.append({
        "role": "user",
        "content": besked
    })

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "Du er AK-AI-Partner. "
            "Du hjælper brugeren klart, praktisk og på dansk.\n\n"
            "Langtidshukommelse om brugeren:\n"
            f"{kendte_fakta}"
        ),
        input=samtale,
    )

    svar = response.output_text

    samtale.append({
        "role": "assistant",
        "content": svar
    })

    gem_json(HUKOMMELSESFIL, samtale)

    print(f"\nAK-AI-Partner: {svar}\n")