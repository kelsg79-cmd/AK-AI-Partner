import json
import os
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

load_dotenv()
client = OpenAI()

FAKTAFIL = "facts.json"
CHATFIL = "chat_history.json"
PROFILFIL = "partner_profile.txt"


def hent_json(filnavn, standard):
    if os.path.exists(filnavn):
        with open(filnavn, "r", encoding="utf-8") as fil:
            return json.load(fil)
    return standard


def gem_json(filnavn, data):
    with open(filnavn, "w", encoding="utf-8") as fil:
        json.dump(data, fil, ensure_ascii=False, indent=2)


def hent_partnerprofil():
    if os.path.exists(PROFILFIL):
        with open(PROFILFIL, "r", encoding="utf-8") as fil:
            return fil.read()

    return (
        "Du er AK-AI-Partner. "
        "Du hjælper brugeren klart, praktisk og på dansk."
    )


def foreslaa_hukommelse(besked):
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "Vurder om brugerens besked indeholder en stabil oplysning, "
            "som kan være nyttig at huske i fremtidige samtaler. "
            "Gem aldrig passwords, API-nøgler eller andre hemmeligheder. "
            "Hvis intet bør huskes, svar præcis: INGEN. "
            "Ellers svar kun med én kort sætning."
        ),
        input=besked,
    )

    forslag = response.output_text.strip()

    if forslag.upper() == "INGEN":
        return None

    return forslag


def laes_pdf(fil):
    reader = PdfReader(BytesIO(fil.getvalue()))
    sider = []

    for nummer, side in enumerate(reader.pages, start=1):
        tekst = side.extract_text()

        if tekst:
            sider.append(
                f"--- PDF side {nummer} ---\n{tekst}"
            )

    return "\n\n".join(sider)


def laes_word(fil):
    document = Document(BytesIO(fil.getvalue()))
    dele = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            dele.append(paragraph.text)

    for tabel in document.tables:
        for row in tabel.rows:
            celler = [
                celle.text.strip()
                for celle in row.cells
            ]
            dele.append(" | ".join(celler))

    return "\n".join(dele)


def laes_excel(fil):
    workbook = load_workbook(
        BytesIO(fil.getvalue()),
        data_only=True,
        read_only=True,
    )

    dele = []

    for sheet in workbook.worksheets:
        dele.append(
            f"--- Excel-ark: {sheet.title} ---"
        )

        for row in sheet.iter_rows(values_only=True):
            vaerdier = [
                "" if celle is None else str(celle)
                for celle in row
            ]

            if any(vaerdier):
                dele.append(" | ".join(vaerdier))

    return "\n".join(dele)


def laes_powerpoint(fil):
    presentation = Presentation(BytesIO(fil.getvalue()))
    dele = []

    for slide_nummer, slide in enumerate(
        presentation.slides,
        start=1,
    ):
        dele.append(
            f"--- PowerPoint slide {slide_nummer} ---"
        )

        for shape in slide.shapes:
            if hasattr(shape, "text"):
                tekst = shape.text.strip()

                if tekst:
                    dele.append(tekst)

        if slide.has_notes_slide:
            notes_slide = slide.notes_slide

            for shape in notes_slide.shapes:
                if hasattr(shape, "text"):
                    tekst = shape.text.strip()

                    if tekst:
                        dele.append(
                            f"Noter: {tekst}"
                        )

    return "\n".join(dele)


def laes_tekstfil(fil):
    data = fil.getvalue()

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(
            "latin-1",
            errors="replace",
        )


def laes_vedhaeftning(fil):
    navn = fil.name.lower()

    if navn.endswith(".pdf"):
        return laes_pdf(fil)

    if navn.endswith(".docx"):
        return laes_word(fil)

    if navn.endswith(".xlsx"):
        return laes_excel(fil)

    if navn.endswith(".pptx"):
        return laes_powerpoint(fil)

    if navn.endswith(".txt"):
        return laes_tekstfil(fil)

    raise ValueError(
        f"Filtypen understøttes ikke: {fil.name}"
    )


def analyser_mail(mailtekst, dokumenter):
    dokumenttekst = []

    for dokument in dokumenter:
        dokumenttekst.append(
            f"\n===== VEDHÆFTNING: "
            f"{dokument['navn']} =====\n"
            f"{dokument['tekst']}"
        )

    samlet_input = (
        "EMAIL:\n"
        f"{mailtekst}\n\n"
        "VEDHÆFTNINGER:\n"
        + "\n\n".join(dokumenttekst)
    )

    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            f"{partnerprofil}\n\n"
            "Du analyserer en email og dens "
            "vedhæftninger som ét samlet materiale. "
            "Skeln tydeligt mellem oplysninger fra "
            "mailen og oplysninger fra vedhæftningerne. "
            "Du må aldrig opfinde manglende oplysninger. "
            "Hvis noget ikke fremgår, skriv "
            "'Ikke angivet'.\n\n"

            "Returner analysen med disse overskrifter:\n\n"

            "## Kort resume\n"
            "Højst 5 linjer.\n\n"

            "## Vigtige punkter\n"
            "De vigtigste oplysninger.\n\n"

            "## Handlinger\n"
            "Hvad skal gøres og af hvem, hvis det fremgår.\n\n"

            "## Deadlines\n"
            "Datoer, tidsfrister og aftaler.\n\n"

            "## Afventer\n"
            "Hvad vi venter på fra andre.\n\n"

            "## Vedhæftninger\n"
            "Forklar kort hvad hver vedhæftning "
            "indeholder, og hvorfor den er relevant.\n\n"

            "## Risici og opmærksomhedspunkter\n"
            "Problemer, uklarheder eller risici.\n\n"

            "## Prioritet\n"
            "Vælg HØJ, MELLEM eller LAV og forklar kort."
        ),
        input=samlet_input,
    )

    return response.output_text


partnerprofil = hent_partnerprofil()

st.set_page_config(
    page_title="AK-AI-Partner",
    page_icon="🤖",
    layout="wide",
)

st.title("AK-AI-Partner")
st.caption("Din personlige AI-arbejdspartner")


if "facts" not in st.session_state:
    st.session_state.facts = hent_json(
        FAKTAFIL,
        [],
    )

if "messages" not in st.session_state:
    st.session_state.messages = hent_json(
        CHATFIL,
        [],
    )

if "memory_suggestion" not in st.session_state:
    st.session_state.memory_suggestion = None


with st.sidebar:
    st.header("AK-AI-Partner")

    side = st.radio(
        "Vælg funktion",
        [
            "Chat",
            "Analyser mail",
            "Hukommelse",
        ],
    )

    if st.button("Ryd chat"):
        st.session_state.messages = []
        gem_json(CHATFIL, [])
        st.session_state.memory_suggestion = None
        st.rerun()


if side == "Chat":
    st.header("Chat")

    if st.session_state.memory_suggestion:
        st.info(
            "AK-AI-Partner foreslår at huske:\n\n"
            + st.session_state.memory_suggestion
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Ja, husk det"):
                forslag = (
                    st.session_state.memory_suggestion
                )

                if forslag not in st.session_state.facts:
                    st.session_state.facts.append(
                        forslag
                    )
                    gem_json(
                        FAKTAFIL,
                        st.session_state.facts,
                    )

                st.session_state.memory_suggestion = None
                st.rerun()

        with col2:
            if st.button("Nej tak"):
                st.session_state.memory_suggestion = None
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    besked = st.chat_input(
        "Skriv til AK-AI-Partner..."
    )

    if besked:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": besked,
            }
        )

        gem_json(
            CHATFIL,
            st.session_state.messages,
        )

        kendte_fakta = "\n".join(
            f"- {faktum}"
            for faktum in st.session_state.facts
        )

        response = client.responses.create(
            model="gpt-5.4-mini",
            instructions=(
                f"{partnerprofil}\n\n"
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

        gem_json(
            CHATFIL,
            st.session_state.messages,
        )

        forslag = foreslaa_hukommelse(
            besked
        )

        if (
            forslag
            and forslag
            not in st.session_state.facts
        ):
            st.session_state.memory_suggestion = (
                forslag
            )

        st.rerun()


elif side == "Analyser mail":
    st.header("Analyser mail")

    st.write(
        "Indsæt en email og upload eventuelle "
        "vedhæftninger. AK-AI-Partner analyserer "
        "det hele samlet."
    )

    mailtekst = st.text_area(
        "Email",
        height=280,
        placeholder="Indsæt emailens tekst her...",
    )

    uploaded_files = st.file_uploader(
        "Vedhæftninger",
        type=[
            "pdf",
            "docx",
            "xlsx",
            "pptx",
            "txt",
        ],
        accept_multiple_files=True,
    )

    dokumenter = []

    if uploaded_files:
        st.subheader("Vedhæftninger")

        for fil in uploaded_files:
            try:
                tekst = laes_vedhaeftning(fil)

                dokumenter.append(
                    {
                        "navn": fil.name,
                        "tekst": tekst,
                    }
                )

                if tekst.strip():
                    st.success(
                        f"{fil.name} er læst."
                    )
                else:
                    st.warning(
                        f"{fil.name} indeholder "
                        "ingen læsbar tekst."
                    )

            except Exception as fejl:
                st.error(
                    f"Kunne ikke læse "
                    f"{fil.name}: {fejl}"
                )

    if st.button(
        "Analyser mail",
        type="primary",
    ):
        if (
            not mailtekst.strip()
            and not dokumenter
        ):
            st.warning(
                "Indsæt en email eller "
                "upload mindst én vedhæftning."
            )

        else:
            with st.spinner(
                "Analyserer mail og dokumenter..."
            ):
                analyse = analyser_mail(
                    mailtekst,
                    dokumenter,
                )

            st.subheader("Analyse")
            st.markdown(analyse)


elif side == "Hukommelse":
    st.header("Hukommelse")

    ny_fakta = st.text_input(
        "Noget partneren skal huske"
    )

    if st.button("Gem i hukommelsen"):
        if ny_fakta.strip():
            st.session_state.facts.append(
                ny_fakta.strip()
            )

            gem_json(
                FAKTAFIL,
                st.session_state.facts,
            )

            st.rerun()

    if st.session_state.facts:
        st.write("Partneren husker:")

        for i, faktum in enumerate(
            st.session_state.facts
        ):
            col1, col2 = st.columns(
                [5, 1]
            )

            with col1:
                st.write(faktum)

            with col2:
                if st.button(
                    "Slet",
                    key=f"slet_{i}",
                ):
                    st.session_state.facts.pop(i)

                    gem_json(
                        FAKTAFIL,
                        st.session_state.facts,
                    )

                    st.rerun()

    else:
        st.info(
            "Ingen gemte fakta endnu."
        )