print("AK-AI-Partner er startet.")
print("Skriv 'stop' for at afslutte.\n")

while True:
    besked = input("Dig: ")

    if besked.lower() == "stop":
        print("AK-AI-Partner: Vi ses!")
        break

    print(f"AK-AI-Partner: Du skrev: {besked}")