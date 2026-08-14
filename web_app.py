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


def foreslaa_hukommelse(besked):
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "Vurder om brugerens besked indeholder en stabil oplysning, "
            "som kan være nyttig at huske i fremtidige samtaler. "
            "Eksempler er præferencer, mål, projekter eller arbejdsmetoder. "
            "Gem ikke passwords, API-nøgler eller andre hemmeligheder. "
            "Hvis intet bør huskes, svar præcis: INGEN. "
            "Ellers svar kun med én kort sætning, der beskriver faktummet."
        ),
        input=besked,
    )

    forslag = response.output_text.strip()

    if forslag.upper() == "INGEN":
        return None

    return forslag


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

if "memory_suggestion" not in st.session_state:
    st.session_state.memory_suggestion = None


with st.sidebar:
    st.header("Hukommelse")

    ny_fakta = st.text_input("Noget partneren skal huske")

    if st.button("Gem i hukommelsen"):
        if ny_fakta.strip():
            st.session_state.facts.append(ny_fakta.strip())
            gem_fakta(st.session_state.facts)
            st.rerun()

    if st.session_state.facts:
        st.write("Partneren husker:")

        for i, faktum in enumerate(st.session_state.facts):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(faktum)

            with col2:
                if st.button("Slet", key=f"slet_{i}"):
                    st.session_state.facts.pop(i)
                    gem_fakta(st.session_state.facts)
                    st.rerun()

    else:
        st.write("Ingen gemte fakta endnu.")

    if st.button("Ryd chat"):
        st.session_state.messages = []
        st.session_state.memory_suggestion = None
        st.rerun()


if st.session_state.memory_suggestion:
    st.info(
        "AK-AI-Partner foreslår at huske:\n\n"
        + st.session_state.memory_suggestion
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Ja, husk det"):
            forslag = st.session_state.memory_suggestion

            if forslag not in st.session_state.facts:
                st.session_state.facts.append(forslag)
                gem_fakta(st.session_state.facts)

            st.session_state.memory_suggestion = None
            st.rerun()

    with col2:
        if st.button("Nej tak"):
            st.session_state.memory_suggestion = None
            st.rerun()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


besked = st.chat_input("Skriv til AK-AI-Partner...")

if besked:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": besked,
        }
    )

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

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": svar,
        }
    )

    forslag = foreslaa_hukommelse(besked)

    if forslag and forslag not in st.session_state.facts:
        st.session_state.memory_suggestion = forslag

    st.rerun()