import math
import os
import random
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
# Systèmes : Morse, CASSIS K6, alphabet phonétique OTAN, sémaphore.
# Le sémaphore est à comparer avec un tableau officiel scout.
# ============================================================

# --- Compatibilité Streamlit : use_container_width est déprécié ---
try:
    from packaging.version import Version

    _NEW_ST = Version(st.__version__) >= Version("1.50")
except Exception:
    _NEW_ST = False
STRETCH = {"width": "stretch"} if _NEW_ST else {"use_container_width": True}

# Option demandée : "- -" (deux traits séparés) se décode en M, pas en TT.
# Mets False pour revenir au comportement Morse standard.
MORSE_SPLIT_M = True

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

# CASSIS K6 : K=06 ... Z=21, A=22 ... E=26, F=01 ... J=05
K6 = {
    "A": "22", "B": "23", "C": "24", "D": "25", "E": "26",
    "F": "01", "G": "02", "H": "03", "I": "04", "J": "05",
    "K": "06", "L": "07", "M": "08", "N": "09", "O": "10",
    "P": "11", "Q": "12", "R": "13", "S": "14", "T": "15",
    "U": "16", "V": "17", "W": "18", "X": "19", "Y": "20",
    "Z": "21",
}
K6_INV = {v: k for k, v in K6.items()}

# Sémaphore : (bras gauche, bras droit) du point de vue de l'émetteur.
SEMAPHORE = {
    "A": ("DOWN", "LOW"),       "B": ("DOWN", "OUT"),
    "C": ("DOWN", "HIGH"),      "D": ("DOWN", "UP"),
    "E": ("HIGH", "DOWN"),      "F": ("OUT", "DOWN"),
    "G": ("LOW", "DOWN"),       "H": ("ACROSS_LOW", "OUT"),
    "I": ("ACROSS_LOW", "HIGH"),  "J": ("OUT", "UP"),
    "K": ("UP", "LOW"),         "L": ("HIGH", "LOW"),
    "M": ("OUT", "LOW"),        "N": ("LOW", "LOW"),
    "O": ("ACROSS_HIGH", "OUT"), "P": ("UP", "OUT"),
    "Q": ("HIGH", "OUT"),       "R": ("OUT", "OUT"),
    "S": ("LOW", "OUT"),        "T": ("UP", "HIGH"),
    "U": ("HIGH", "HIGH"),      "V": ("LOW", "UP"),
    "W": ("OUT", "ACROSS_HIGH"), "X": ("LOW", "ACROSS_HIGH"),
    "Y": ("OUT", "HIGH"),       "Z": ("OUT", "ACROSS_LOW"),
}
# Vecteurs (x, y) de chaque position, vus de dos : la gauche de l'émetteur
# est à gauche de l'image, y positif = vers le bas.
ARM_VEC = {
    "left": {
        "DOWN": (0, 1), "LOW": (-1, 1), "OUT": (-1, 0), "HIGH": (-1, -1),
        "UP": (0, -1), "ACROSS_LOW": (1, 1), "ACROSS_HIGH": (1, -1),
    }
}
ARM_VEC["right"] = {k: (-x, y) for k, (x, y) in ARM_VEC["left"].items()}


def pair_key(left, right):
    """Clé indépendante de l'ordre des bras (positions physiques)."""
    return frozenset({ARM_VEC["left"][left], ARM_VEC["right"][right]})


SEMAPHORE_INV = {pair_key(l, r): k for k, (l, r) in SEMAPHORE.items()}
if len(SEMAPHORE_INV) != 26:
    st.warning("Table sémaphore incohérente : deux lettres ont la même position.")

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

CHAR_REPLACEMENTS = {
    "’": "'", "‘": "'", "`": "'", "´": "'",
    "“": '"', "”": '"', "«": '"', "»": '"',
    "–": "-", "—": "-", "…": "...",
    "Œ": "OE", "Æ": "AE", "ß": "SS",
}


def normalize_text(value: str) -> str:
    """Majuscules, accents retirés, ponctuation typographique simplifiée."""
    value = value.upper()
    for old, new in CHAR_REPLACEMENTS.items():
        value = value.replace(old, new)
    value = unicodedata.normalize("NFD", value)
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


def encode_generic(text, table, name):
    text = normalize_text(text)
    validate_chars(text, set(table), name)
    return " / ".join(
        " ".join(table[ch] for ch in word) for word in text.split(" ")
    )


def decode_generic(text, inverse, error_label, prepare=None, normalize=False):
    """Décodage commun : mots séparés par /, symboles séparés par des espaces."""
    text = normalize_text(text) if normalize else text.strip()
    if not text:
        return ""
    result = []
    for word in re.split(r"\s*/\s*", text):
        tokens = word.split()
        if prepare:
            tokens = prepare(tokens)
        unknown = [t for t in tokens if t not in inverse]
        if unknown:
            raise ValueError(f"{error_label} : " + ", ".join(unknown))
        result.append("".join(inverse[t] for t in tokens))
    return " ".join(result)


def merge_split_m(tokens):
    """Deux traits isolés consécutifs ('-' '-') deviennent M ('--')."""
    out, i = [], 0
    while i < len(tokens):
        if tokens[i] == "-" and i + 1 < len(tokens) and tokens[i + 1] == "-":
            out.append("--")
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out


def morse_encode(text):
    return encode_generic(text, MORSE, "Le Morse")


def morse_decode(text):
    return decode_generic(
        text,
        MORSE_INV,
        "Code Morse inconnu",
        prepare=merge_split_m if MORSE_SPLIT_M else None,
    )


def k6_encode(text):
    return encode_generic(text, K6, "Le code CASSIS K6")


def k6_prepare(tokens):
    return [t.zfill(2) if t.isdigit() else t for t in tokens]


def k6_decode(text):
    return decode_generic(text, K6_INV, "Nombre K6 inconnu", prepare=k6_prepare)


def phonetic_encode(text):
    return encode_generic(text, NATO, "L'alphabet phonétique")


def phonetic_decode(text):
    return decode_generic(
        text, NATO_INV, "Mot phonétique inconnu", normalize=True
    )


def semaphore_description(letter):
    left, right = SEMAPHORE[letter]
    return f"{letter} : gauche {POSITION_FR[left]}, droite {POSITION_FR[right]}"


def semaphore_encode(text):
    """Texte de description en français (les images sont affichées à part)."""
    text = normalize_text(text)
    validate_chars(text, set(SEMAPHORE), "Le sémaphore")
    return " / ".join(
        " | ".join(semaphore_description(l) for l in word)
        for word in text.split(" ")
    )


def semaphore_decode(text):
    """Le message est composé lettre par lettre avec le sélecteur d'images."""
    text = normalize_text(text)
    validate_chars(text, set(SEMAPHORE), "Le sémaphore")
    return text


# --- Dessin des signaux (SVG généré, aucun fichier image nécessaire) ---

FLAG_COLORS = {"left": "#d62828", "right": "#f2c230"}


def semaphore_svg_pair(left, right, size=84):
    sx, sy = 50, 48
    stroke = 'stroke="#f4f4f7" stroke-width="3" stroke-linecap="round"'
    parts = [
        '<circle cx="50" cy="33" r="7" fill="none" stroke="#f4f4f7" stroke-width="2.5"/>',
        f'<line x1="50" y1="40" x2="50" y2="85" {stroke}/>',
        f'<line x1="50" y1="85" x2="42" y2="115" {stroke}/>',
        f'<line x1="50" y1="85" x2="58" y2="115" {stroke}/>',
    ]
    flags = []
    for side, pos in (("left", left), ("right", right)):
        vx, vy = ARM_VEC[side][pos]
        norm = math.hypot(vx, vy)
        dx, dy = vx / norm, vy / norm
        ex, ey = sx + 32 * dx, sy + 32 * dy
        nx, ny = -dy, dx
        outward = -1 if side == "left" else 1
        if abs(nx) > 1e-6:
            if nx * outward < 0:
                nx, ny = -nx, -ny
        elif ny < 0:
            nx, ny = -nx, -ny
        bx, by = sx + 14 * dx, sy + 14 * dy
        pts = [(bx, by), (ex, ey), (ex + 12 * nx, ey + 12 * ny),
               (bx + 12 * nx, by + 12 * ny)]
        pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        parts.append(
            f'<line x1="{sx}" y1="{sy}" x2="{ex:.1f}" y2="{ey:.1f}" {stroke}/>'
        )
        flags.append(
            f'<polygon points="{pts_str}" fill="{FLAG_COLORS[side]}" '
            'stroke="#11111f" stroke-width="1"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" '
        f'width="{size}" height="{int(size * 1.2)}">'
        + "".join(parts + flags) + "</svg>"
    )


def semaphore_gallery(text, size=84):
    """HTML : une image par lettre, un espace par espace."""
    cells = []
    for ch in text:
        if ch == " ":
            cells.append('<div style="width:28px"></div>')
        elif ch in SEMAPHORE:
            left, right = SEMAPHORE[ch]
            cells.append(
                '<div style="text-align:center">'
                + semaphore_svg_pair(left, right, size)
                + f'<div style="color:#e5bd62;font-weight:700">{ch}</div></div>'
            )
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end">'
        + "".join(cells) + "</div>"
    )


def semaphore_builder():
    """Compose un message en choisissant la position de chaque bras."""
    positions = list(POSITION_FR)
    seq = st.session_state.get("fauco_sema_seq", "")
    c1, c2 = st.columns(2)
    left = c1.selectbox(
        "Bras gauche (drapeau rouge)", positions, index=0,
        format_func=POSITION_FR.get, key="fauco_sema_left",
    )
    right = c2.selectbox(
        "Bras droit (drapeau jaune)", positions, index=1,
        format_func=POSITION_FR.get, key="fauco_sema_right",
    )
    letter = SEMAPHORE_INV.get(pair_key(left, right))
    st.markdown(
        '<div style="text-align:center">'
        + semaphore_svg_pair(left, right, 120) + "</div>",
        unsafe_allow_html=True,
    )
    if letter:
        st.caption(f"Ce signal = lettre {letter}")
    else:
        st.caption("Cette position ne correspond à aucune lettre.")

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("➕ Lettre", key="fauco_sema_add"):
        if letter:
            seq += letter
    if b2.button("␣ Espace", key="fauco_sema_space"):
        if seq and not seq.endswith(" "):
            seq += " "
    if b3.button("⌫ Retour", key="fauco_sema_back"):
        seq = seq[:-1]
    if b4.button("🗑️ Vider", key="fauco_sema_clear"):
        seq = ""
    st.session_state["fauco_sema_seq"] = seq

    st.write("**Signaux composés :**")
    if seq.strip():
        st.markdown(semaphore_gallery(seq, 70), unsafe_allow_html=True)
    else:
        st.caption("Aucun signal pour le moment.")
    return seq


# ------------------------- QUIZ ------------------------------

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def build_letter_quiz(theme, mapping, display):
    """52 questions par code (26 lettres x 2 sens), options mélangées
    de façon déterministe (même ordre à chaque rerun)."""
    bank = []
    for letter in LETTERS:
        value = display(mapping[letter])
        others = [l for l in LETTERS if l != letter]

        rng = random.Random(f"{theme}-code-{letter}")
        wrong = [display(mapping[l]) for l in rng.sample(others, 3)]
        options = [value] + wrong
        rng.shuffle(options)
        bank.append({
            "question": f"Quel est le code de la lettre {letter} ?",
            "options": options,
            "answer": value,
            "explanation": f"La lettre {letter} correspond à {value}.",
        })

        rng = random.Random(f"{theme}-lettre-{letter}")
        options = [letter] + rng.sample(others, 3)
        rng.shuffle(options)
        bank.append({
            "question": f"Tu reçois le signal {value}. Quelle lettre notes-tu ?",
            "options": options,
            "answer": letter,
            "explanation": f"Le signal {value} représente la lettre {letter}.",
        })
    return bank


def build_semaphore_quiz():
    """52 questions : image -> lettre, puis lettre -> description."""
    bank = []
    for letter in LETTERS:
        others = [l for l in LETTERS if l != letter]
        left, right = SEMAPHORE[letter]
        desc = f"gauche {POSITION_FR[left]}, droite {POSITION_FR[right]}"

        rng = random.Random(f"sema-img-{letter}")
        options = [letter] + rng.sample(others, 3)
        rng.shuffle(options)
        bank.append({
            "question": "Quelle lettre ce signal représente-t-il ?",
            "image": letter,
            "answer_letter": letter,
            "options": options,
            "answer": letter,
            "explanation": f"Ce signal est la lettre {letter} ({desc}).",
        })

        rng = random.Random(f"sema-desc-{letter}")
        wrong = [
            f"gauche {POSITION_FR[SEMAPHORE[l][0]]}, droite {POSITION_FR[SEMAPHORE[l][1]]}"
            for l in rng.sample(others, 3)
        ]
        options = [desc] + wrong
        rng.shuffle(options)
        bank.append({
            "question": f"Quel est le signal de la lettre {letter} ?",
            "image": None,
            "answer_letter": letter,
            "options": options,
            "answer": desc,
            "explanation": f"La lettre {letter} : {desc}.",
        })
    return bank


quiz = {
    "Morse": build_letter_quiz("morse", MORSE, lambda v: v),
    "CASSIS K6": build_letter_quiz("k6", K6, lambda v: v),
    "Alphabet phonétique OTAN": build_letter_quiz("nato", NATO, lambda v: v),
    "Sémaphore": build_semaphore_quiz(),
}


def get_quiz_state(theme):
    states = st.session_state.setdefault("fauco_quiz_state", {})
    if theme not in states:
        order = list(range(len(quiz[theme])))
        random.shuffle(order)
        states[theme] = {"order": order, "pos": 0, "feedback": None, "round": 0}
    return states[theme]


# ------------------------- INTERFACE -------------------------

st.title("⚜️ FAUCO CODE")
st.subheader("GÉNIE INFORMATIQUE")
st.caption("TOUJOURS PRÊT ! | Version 3.1 — Codes scouts")

st.info(
    "Cette version propose quatre systèmes de transmission : "
    "Morse, CASSIS K6, alphabet phonétique OTAN et sémaphore."
)

st.divider()
st.header("🎓 MODE APPRENTISSAGE SCOUT")
st.write(
    "Apprends les quatre moyens de transmission, puis vérifie tes "
    "connaissances avec un mini-quiz. Chaque bonne réponse rapporte 1 point."
)

lessons = {
    "Morse": (
        "Le Morse représente les lettres et les chiffres avec des points (.) "
        "et des traits (-). Dans cette application, les lettres d'un même mot "
        "sont séparées par des espaces et les mots par une barre oblique (/). "
        "Deux traits séparés ( - - ) sont lus comme la lettre M.",
        "Exemple : SOS = ... --- ...  |  M = --",
    ),
    "CASSIS K6": (
        "Le CASSIS K6 associe chaque lettre à un nombre à deux chiffres. "
        "La suite commence à K=06, continue jusqu'à Z=21, puis A=22 jusqu'à "
        "E=26, et enfin F=01 jusqu'à J=05.",
        "Exemple : A=22, B=23, C=24. Donc ABC = 22 23 24.",
    ),
    "Alphabet phonétique OTAN": (
        "L'alphabet phonétique international OTAN remplace chaque lettre "
        "par un mot prononcé à la radio pour éviter les confusions.",
        "Exemple : A=ALFA, B=BRAVO, C=CHARLIE.",
    ),
    "Sémaphore": (
        "Le sémaphore transmet les lettres grâce à deux drapeaux tenus "
        "dans des positions précises. Chaque lettre correspond à une "
        "combinaison des deux bras.",
        "Les dessins montrent l'émetteur vu de dos : bras gauche à gauche "
        "(drapeau rouge), bras droit à droite (drapeau jaune). "
        "Exemple : A = bras gauche vers le bas, bras droit en diagonale basse.",
    ),
}

with st.expander("📘 Les 4 petites leçons", expanded=True):
    lesson_choice = st.selectbox(
        "Choisis une leçon", list(lessons.keys()), key="fauco_lesson_choice"
    )
    st.markdown(f"**{lesson_choice}**")
    st.write(lessons[lesson_choice][0])
    st.info(lessons[lesson_choice][1])
    if lesson_choice == "Sémaphore":
        st.markdown(semaphore_gallery("ABC", 90), unsafe_allow_html=True)

st.subheader("📝 Quiz scout")
quiz_choice = st.selectbox(
    "Choisis le thème du quiz", list(quiz.keys()), key="fauco_quiz_choice"
)
state = get_quiz_state(quiz_choice)
bank = quiz[quiz_choice]
total = len(bank)
question = bank[state["order"][state["pos"] % total]]

st.caption(f"Question {state['pos'] % total + 1} sur {total}.")
st.write(f"**{question['question']}**")
if question.get("image"):
    st.markdown(semaphore_gallery(question["image"], 120), unsafe_allow_html=True)

widget_key = f"fauco_answer_{quiz_choice}_{state['round']}_{state['pos']}"
answered = state["feedback"] is not None
answer = st.radio(
    "Ta réponse",
    question["options"],
    index=None,
    key=widget_key,
    disabled=answered,
)

if not answered:
    if st.button("Valider ma réponse", key=f"fauco_validate_{widget_key}"):
        if answer is None:
            st.warning("Choisis une réponse avant de valider.")
        else:
            correct = answer == question["answer"]
            state["feedback"] = (correct, question["explanation"])
            st.session_state["fauco_quiz_attempts"] = (
                st.session_state.get("fauco_quiz_attempts", 0) + 1
            )
            if correct:
                st.session_state["fauco_quiz_score"] = (
                    st.session_state.get("fauco_quiz_score", 0) + 1
                )
            st.rerun()
else:
    correct, explanation = state["feedback"]
    if correct:
        st.success("Bonne réponse ! " + explanation)
    else:
        st.error("Pas tout à fait. " + explanation)
    if question.get("answer_letter"):
        st.markdown(
            semaphore_gallery(question["answer_letter"], 100),
            unsafe_allow_html=True,
        )
    if st.button("➡️ Question suivante", key=f"fauco_next_{widget_key}"):
        state["pos"] += 1
        state["feedback"] = None
        st.rerun()

score = st.session_state.get("fauco_quiz_score", 0)
attempts = st.session_state.get("fauco_quiz_attempts", 0)
st.metric("⭐ Ton score", f"{score} / {attempts}")

if st.button("🔄 Nouveau quiz — mélanger et remettre le score à zéro",
             key="fauco_reset_quiz"):
    st.session_state["fauco_quiz_score"] = 0
    st.session_state["fauco_quiz_attempts"] = 0
    new_round = state["round"] + 1
    for theme in quiz:
        order = list(range(len(quiz[theme])))
        random.shuffle(order)
        st.session_state["fauco_quiz_state"][theme] = {
            "order": order, "pos": 0, "feedback": None, "round": new_round,
        }
    st.rerun()

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
    st.caption(
        "Codage : points (.) et traits (-). Les mots sont séparés par /. "
        "Deux traits séparés ( - - ) donnent M."
    )
elif system == "CASSIS K6 — CODE SCOUT":
    st.caption("Code scout CASSIS : K=06, L=07, …, Z=21, A=22, …, J=05.")
elif system == "ALPHABET PHONÉTIQUE OTAN":
    st.caption(
        "Chaque lettre est remplacée par son mot radio international : "
        "ALFA, BRAVO, CHARLIE…"
    )
else:
    st.caption(
        "Chaque lettre est un dessin : bras gauche (drapeau rouge) et bras "
        "droit (drapeau jaune), vus de dos. Pour décoder, compose le signal "
        "avec les deux listes."
    )

if system == "SÉMAPHORE INTERNATIONAL" and mode == "Décoder":
    message = semaphore_builder()
else:
    message = st.text_area(
        "Ton message",
        height=150,
        placeholder=(
            "Écris ton texte ici…" if mode == "Coder" else "Colle ici le message codé…"
        ),
    )

if st.button("⚡ EXÉCUTER", **STRETCH):
    if not message.strip():
        st.warning("Entre un message avant de lancer l'opération.")
    else:
        function = systems[system][0 if mode == "Coder" else 1]
        try:
            output = function(message)
            st.session_state["fauco_result"] = output
            st.session_state["fauco_result_sema"] = (
                normalize_text(message)
                if system == "SÉMAPHORE INTERNATIONAL" else None
            )
            history = st.session_state.setdefault("fauco_history", [])
            history.insert(0, {
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "system": system,
                "mode": mode,
                "input": message,
                "output": output,
                "sema": st.session_state["fauco_result_sema"],
            })
            st.session_state["fauco_history"] = history[:30]
            st.success("Opération réussie !")
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"Une erreur inattendue est survenue : {error}")

if "fauco_result" in st.session_state:
    st.subheader("📌 RÉSULTAT")
    if st.session_state.get("fauco_result_sema"):
        st.markdown(
            semaphore_gallery(st.session_state["fauco_result_sema"], 84),
            unsafe_allow_html=True,
        )
    st.code(st.session_state["fauco_result"], language=None)
    st.download_button(
        "⬇️ Télécharger le résultat",
        data=st.session_state["fauco_result"],
        file_name="fauco_code_resultat.txt",
        mime="text/plain",
        **STRETCH,
    )

st.divider()
st.subheader("📖 TABLES DE RÉFÉRENCE")

with st.expander("Morse international"):
    st.table([{"Lettre": k, "Signal": v} for k, v in MORSE.items()])

with st.expander("CASSIS K6 — table scout"):
    if os.path.exists("code_k6_reference.jpg"):
        st.image(
            "code_k6_reference.jpg",
            caption="Tableau CASSIS K6 fourni — référence à consulter",
            **STRETCH,
        )
    else:
        st.caption("Image de référence absente. Table générée :")
        st.table([{"Lettre": k, "Nombre": v} for k, v in K6.items()])

with st.expander("Alphabet phonétique OTAN"):
    st.table([{"Lettre": k, "Mot": v} for k, v in NATO.items()])

with st.expander("Sémaphore — les 26 signaux"):
    st.markdown(
        semaphore_gallery("".join(SEMAPHORE), 70), unsafe_allow_html=True
    )
    st.caption(
        "Vue de dos : bras gauche à gauche (drapeau rouge), bras droit à "
        "droite (drapeau jaune). Compare avec un tableau de sémaphore scout."
    )
    st.table([
        {
            "Lettre": letter,
            "Bras gauche": POSITION_FR[left],
            "Bras droit": POSITION_FR[right],
        }
        for letter, (left, right) in SEMAPHORE.items()
    ])

st.divider()
st.subheader("📚 HISTORIQUE")

history = st.session_state.get("fauco_history", [])
if history:
    for item in history:
        label = f'{item["date"]} — {item["system"]} — {item["mode"]}'
        with st.expander(label):
            if item.get("sema"):
                st.markdown(
                    semaphore_gallery(item["sema"], 70), unsafe_allow_html=True
                )
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
st.caption("Créé par LUCMARTIN, éclaireur de GSM, futur ingénieur de technologie")
st.caption("GSM TOUJOURS PRÊT !")
