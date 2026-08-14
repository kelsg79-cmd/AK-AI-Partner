import json
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

FAKTAFIL = "facts.json"


def hent_fakta():
    if os.path.exists(FAKTAFIL):
        with open(FAKTAFIL, "r", encoding="utf-8") as fil:
            return json.load(fil)
    return []


def gem_fakta(fakta):
    with open(FAKTAFIL, "w", encoding="utf-8") as fil:
        json.dump(fakta, fil, ensure_ascii=False, indent=2)


st.set_page_config(
    page_title="AK-AI-Partner",
    page_icon="🤖",
)

st.title("AK-AI-Partner")
st.caption("Din personlige AI-partner")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "facts" not in st.session_state:
    st.session_state.facts = hent_fakta()

with st.sidebar:
    st.header("Hukommelse")

    ny_fakta = st.text_input("Noget partneren skal huske")

    if st.button("Gem i hukommelsen"):
        if ny_fakta.strip():
            st.session_state.facts.append(ny_fakta.strip())
            gem_fakta(st.session_state.facts)
            st.success("Gemt")

    if st.session_state.facts:
        st.write("Partneren husker:")
        for faktum in st.session_state.facts:
            st.write(f"- {faktum}")
    else:
        st.write("Ingen gemte fakta endnu.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

besked = st.chat_input("Skriv til AK-AI-Partner...")

if besked:
    st.session_state.messages.append({
        "role": "user",
        "content": besked,
    })

    with st.chat_message("user"):
        st.write(besked)

    kendte_fakta = "\n".join(
        f"- {faktum}" for faktum in st.session_state.facts
    )

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "Du er AK-AI-Partner. "
            "Du hjælper brugeren klart, praktisk og på dansk.\n\n"
            "Langtidshukommelse om brugeren:\n"
            f"{kendte_fakta}"
        ),
        input=st.session_state.messages,
    )

    svar = response.output_text

    st.session_state.messages.append({
        "role": "assistant",
        "content": svar,
    })

    with st.chat_message("assistant"):
        st.write(svar)