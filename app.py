import re
import unicodedata
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="FAUCO CODE",
    page_icon="⚜️",
    layout="centered",
)

# ============================================================
# FAUCO CODE — outils de transmission scoute
# Codes vérifiés : Morse, Cassis K6, alphabet phonétique OTAN,
# sémaphore international.
# ============================================================

st.markdown(
    """
    <style>
    .stApp { background: #11111f; color: #f4f4f7; }
    h1, h2, h3 { color: #e5bd62 !important; }
    p, label, [data-testid="stWidgetLabel"] p { color: #eeeeF4 !important; }
    .stButton button, .stDownloadButton button {
        background: #c49a43; color: #11111f; font-weight: 700;
        border: 1px solid #dfb95e; border-radius: 10px;
    }
    .stTextArea textarea, .stTextInput input {
        background: #f3f4f8; color: #171725; border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------- TABLES ----------------------------

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "$": "...-..-", "@": ".--.-.",
}
MORSE_INV = {v: k for k, v in MORSE.items()}

# Alphabet phonétique international OTAN (orthographe officielle)
NATO = {
    "A": "ALFA", "B": "BRAVO", "C": "CHARLIE", "D": "DELTA",
    "E": "ECHO", "F": "FOXTROT", "G": "GOLF", "H": "HOTEL",
    "I": "INDIA", "J": "JULIETT", "K": "KILO", "L": "LIMA",
    "M": "MIKE", "N": "NOVEMBER", "O": "OSCAR", "P": "PAPA",
    "Q": "QUEBEC", "R": "ROMEO", "S": "SIERRA", "T": "TANGO",
    "U": "UNIFORM", "V": "VICTOR", "W": "WHISKEY", "X": "X-RAY",
    "Y": "YANKEE", "Z": "ZULU",
}
NATO_INV = {v: k for k, v in NATO.items()}

# Code scout CASSIS K6 : K=6, L=7 ... Z=21, A=22 ... J=5
K6 = {
    "A": "22", "B": "23", "C": "24", "D": "25", "E": "26",
    "F": "01", "G": "02", "H": "03", "I": "04", "J": "05",
    "K": "06", "L": "07", "M": "08", "N": "09", "O": "10",
    "P": "11", "Q": "12", "R": "13", "S": "14", "T": "15",
    "U": "16", "V": "17", "W": "18", "X": "19", "Y": "20",
    "Z": "21",
}
K6_INV = {v: k for k, v in K6.items()}

# Sémaphore international : positions du bras gauche et du bras droit
# décrites du point de vue de la personne qui émet le signal.
# La table suit les positions publiées dans les tableaux de sémaphore.
SEMAPHORE = {
    "A": ("DOWN", "LOW"),       "B": ("DOWN", "OUT"),
    "C": ("DOWN", "HIGH"),      "D": ("DOWN", "UP"),
    "E": ("HIGH", "DOWN"),      "F": ("OUT", "DOWN"),
    "G": ("LOW", "DOWN"),       "H": ("ACROSS_LOW", "OUT"),
    "I": ("ACROSS_LOW", "UP"),  "J": ("OUT", "UP"),
    "K": ("UP", "LOW"),         "L": ("HIGH", "LOW"),
    "M": ("OUT", "LOW"),        "N": ("LOW", "LOW"),
    "O": ("ACROSS_HIGH", "OUT"),"P": ("UP", "OUT"),
    "Q": ("HIGH", "OUT"),       "R": ("OUT", "OUT"),
    "S": ("LOW", "OUT"),        "T": ("UP", "HIGH"),
    "U": ("HIGH", "HIGH"),      "V": ("LOW", "UP"),
    "W": ("OUT", "ACROSS_HIGH"),"X": ("LOW", "ACROSS_HIGH"),
    "Y": ("OUT", "HIGH"),       "Z": ("OUT", "ACROSS_LOW"),
}
SEMAPHORE_INV = {v: k for k, v in SEMAPHORE.items()}

POSITION_FR = {
    "DOWN": "vers le bas",
    "LOW": "diagonale basse",
    "OUT": "horizontal vers l'extérieur",
    "HIGH": "diagonale haute",
    "UP": "vers le haut",
    "ACROSS_LOW": "croisé devant le corps, bas",
    "ACROSS_HIGH": "croisé devant le corps, haut",
}

# ------------------------- HELPERS ---------------------------

def normalize_text(value: str) -> str:
    """Majuscules, accents retirés, espaces normalisés."""
    value = unicodedata.normalize("NFD", value.upper())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", value).strip()


def validate_chars(text: str, allowed: set, system_name: str) -> None:
    unsupported = sorted({ch for ch in text if ch != " " and ch not in allowed})
    if unsupported:
        chars = ", ".join(repr(ch) for ch in unsupported)
        raise ValueError(
            f"{system_name} ne prend pas en charge : {chars}. "
            "Vérifie l'orthographe ou retire ces caractères."
        )


def morse_encode(text: str) -> str:
    text = normalize_text(text)
    validate_chars(text, set(MORSE), "Le Morse")
    return " / ".join(
        " ".join(MORSE[ch] for ch in word)
        for word in text.split(" ")
    )


def morse_decode(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    words = re.split(r"\s*/\s*", text)
    decoded_words = []
    for word in words:
        tokens = word.split()
        if not tokens:
            decoded_words.append("")
            continue
        unknown = [token for token in tokens if token not in MORSE_INV]
        if unknown:
            raise ValueError("Code Morse inconnu : " + ", ".join(unknown))
        decoded_words.append("".join(MORSE_INV[token] for token in tokens))
    return " ".join(decoded_words)


def k6_encode(text: str) -> str:
    text = normalize_text(text)
    validate_chars(text, set(K6), "Le code CASSIS K6")
    return " / ".join(
        " ".join(K6[ch] for ch in word)
        for word in text.split(" ")
    )


def k6_decode(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    words = re.split(r"\s*/\s*", text)
    result = []
    for word in words:
        tokens = word.split()
        if not tokens:
            result.append("")
            continue
        unknown = [token for token in tokens if token not in K6_INV]
        if unknown:
            raise ValueError("Nombre K6 inconnu : " + ", ".join(unknown))
        result.append("".join(K6_INV[token] for token in tokens))
    return " ".join(result)


def phonetic_encode(text: str) -> str:
    text = normalize_text(text)
    validate_chars(text, set(NATO), "L'alphabet phonétique")
    return " / ".join(
        " ".join(NATO[ch] for ch in word)
        for word in text.split(" ")
    )


def phonetic_decode(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    words = re.split(r"\s*/\s*", text)
    result = []
    for word in words:
        tokens = word.split()
        if not tokens:
            result.append("")
            continue
        unknown = [token for token in tokens if token not in NATO_INV]
        if unknown:
            raise ValueError(
                "Mot phonétique inconnu : " + ", ".join(unknown)
            )
        result.append("".join(NATO_INV[token] for token in tokens))
    return " ".join(result)


def semaphore_encode(text: str) -> str:
    text = normalize_text(text)
    validate_chars(text, set(SEMAPHORE), "Le sémaphore")
    encoded_words = []
    for word in text.split(" "):
        signals = []
        for letter in word:
            left, right = SEMAPHORE[letter]
            signals.append(f"{left}-{right}")
        encoded_words.append(" | ".join(signals))
    return " / ".join(encoded_words)


def semaphore_decode(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    words = re.split(r"\s*/\s*", text)
    result = []
    for word in words:
        tokens = [x.strip().upper() for x in word.split("|") if x.strip()]
        letters = []
        for token in tokens:
            parts = token.split("-")
            if len(parts) != 2:
                raise ValueError(
                    f"Signal sémaphore invalide : {token}. "
                    "Format attendu : DOWN-LOW | DOWN-OUT."
                )
            pair = (parts[0], parts[1])
            if pair not in SEMAPHORE_INV:
                raise ValueError(f"Position sémaphore inconnue : {token}")
            letters.append(SEMAPHORE_INV[pair])
        result.append("".join(letters))
    return " ".join(result)


# ------------------------- INTERFACE -------------------------

st.title("⚜️ FAUCO CODE")
st.subheader("GÉNIE INFORMATIQUE")
st.caption("TOUJOURS PRÊT ! | Version 3.0 — Codes scouts")

st.info(
    "Cette version propose quatre systèmes de transmission : "
    "Morse, CASSIS K6, alphabet phonétique OTAN et sémaphore."
)

st.divider()

systems = {
    "MORSE": (morse_encode, morse_decode),
    "CASSIS K6 — CODE SCOUT": (k6_encode, k6_decode),
    "ALPHABET PHONÉTIQUE OTAN": (phonetic_encode, phonetic_decode),
    "SÉMAPHORE INTERNATIONAL": (semaphore_encode, semaphore_decode),
}

system = st.selectbox("Choisir un système", list(systems))
mode = st.radio("Opération", ["Coder", "Décoder"], horizontal=True)

if system == "MORSE":
    st.caption("Codage : points (.) et traits (-). Les mots sont séparés par /.")
elif system == "CASSIS K6 — CODE SCOUT":
    st.caption("Code scout CASSIS : K=06, L=07, …, Z=21, A=22, …, J=05.")
elif system == "ALPHABET PHONÉTIQUE OTAN":
    st.caption("Chaque lettre est remplacée par son mot radio international : ALFA, BRAVO, CHARLIE…")
else:
    st.caption(
        "Chaque lettre est représentée par la position du bras gauche "
        "et du bras droit de l'émetteur. Exemple : DOWN-LOW."
    )

message = st.text_area(
    "Ton message",
    height=150,
    placeholder=(
        "Écris ton texte ici…"
        if mode == "Coder"
        else "Colle ici le message codé…"
    ),
)

if st.button("⚡ EXÉCUTER", use_container_width=True):
    if not message.strip():
        st.warning("Entre un message avant de lancer l'opération.")
    else:
        function = systems[system][0 if mode == "Coder" else 1]
        try:
            output = function(message)
            st.session_state["fauco_result"] = output
            st.session_state["fauco_last_system"] = system
            st.session_state["fauco_last_mode"] = mode
            history = st.session_state.setdefault("fauco_history", [])
            history.insert(
                0,
                {
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "system": system,
                    "mode": mode,
                    "input": message,
                    "output": output,
                },
            )
            st.session_state["fauco_history"] = history[:30]
            st.success("Opération réussie !")
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"Une erreur inattendue est survenue : {error}")

if "fauco_result" in st.session_state:
    st.subheader("📌 RÉSULTAT")
    st.code(st.session_state["fauco_result"], language=None)
    st.download_button(
        "⬇️ Télécharger le résultat",
        data=st.session_state["fauco_result"],
        file_name="fauco_code_resultat.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.divider()
st.subheader("📖 TABLES DE RÉFÉRENCE")

with st.expander("Morse international"):
    st.table(
        [{"Lettre": key, "Signal": value} for key, value in MORSE.items()]
    )

with st.expander("CASSIS K6 — table scout"):
    st.image(
        "code_k6_reference.jpg",
        caption="Tableau CASSIS K6 fourni — référence à consulter",
        use_container_width=True,
    )

with st.expander("Alphabet phonétique OTAN"):
    st.table(
        [{"Lettre": key, "Mot": value} for key, value in NATO.items()]
    )

with st.expander("Sémaphore — positions des bras"):
    rows = []
    for letter, (left, right) in SEMAPHORE.items():
        rows.append(
            {
                "Lettre": letter,
                "Bras gauche": POSITION_FR[left],
                "Bras droit": POSITION_FR[right],
                "Code technique": f"{left}-{right}",
            }
        )
    st.table(rows)
    st.caption(
        "Les positions sont décrites du point de vue de la personne "
        "qui émet le signal. Pour apprendre le geste, utilise les "
        "illustrations d'un tableau de sémaphore scout."
    )

st.divider()
st.subheader("📚 HISTORIQUE")

history = st.session_state.get("fauco_history", [])
if history:
    for item in history:
        label = f'{item["date"]} — {item["system"]} — {item["mode"]}'
        with st.expander(label):
            st.caption("Message saisi")
            st.code(item["input"], language=None)
            st.caption("Résultat")
            st.code(item["output"], language=None)
    if st.button("🗑️ Effacer l'historique"):
        st.session_state["fauco_history"] = []
        st.rerun()
else:
    st.caption("Aucune opération enregistrée pour le moment.")

st.divider()
st.markdown("### ⚜️ FAUCO CODE")
st.caption("Créer par LUCMARTIN éclaireur de GSM, futur ingénieur de technologie")
st.caption("TOUJOURS PRÊT !")
