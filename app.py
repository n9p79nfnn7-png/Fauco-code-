
import streamlit as st
import string

st.set_page_config(
    page_title="FAUCO CODE",
    page_icon="⚜️",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: #11111f;
    color: white;
}
h1, h2, h3 {
    color: #e5bd62 !important;
}
.stButton button {
    background: #c49a43;
    color: #11111f;
    font-weight: bold;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

MORSE = {
'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..',
'E':'.', 'F':'..-.', 'G':'--.', 'H':'....',
'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..',
'M':'--', 'N':'-.', 'O':'---', 'P':'.--.',
'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-',
'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-',
'Y':'-.--', 'Z':'--..',
'0':'-----', '1':'.----', '2':'..---',
'3':'...--', '4':'....-', '5':'.....',
'6':'-....', '7':'--...', '8':'---..',
'9':'----.'
}

MI = {v:k for k,v in MORSE.items()}

PH = dict(zip(
    string.ascii_uppercase,
    ["ALPHA","BRAVO","CHARLIE","DELTA","ECHO",
     "FOXTROT","GOLF","HOTEL","INDIA","JULIETT",
     "KILO","LIMA","MIKE","NOVEMBER","OSCAR",
     "PAPA","QUEBEC","ROMEO","SIERRA","TANGO",
     "UNIFORM","VICTOR","WHISKEY","XRAY","YANKEE","ZULU"]
))
PHI = {v:k for k,v in PH.items()}

CARRE = {
'11':'A','12':'B','13':'C','14':'D','15':'E',
'21':'F','22':'G','23':'H','24':'I','25':'J',
'31':'K','32':'L','33':'M','34':'N','35':'O',
'41':'P','42':'Q','43':'R','44':'S','45':'T',
'51':'U','52':'V','53':'W','54':'X','55':'Y'
}
CI = {v:k for k,v in CARRE.items()}

HASH = {chr(65+i):f"{i+1:02d}" for i in range(26)}
HI = {v:k for k,v in HASH.items()}

def cesar(t, d):
    return ''.join(
        chr((ord(c)-65+d)%26+65)
        if c in string.ascii_uppercase else c
        for c in t.upper()
    )

def morse_encode(t):
    return " / ".join(
        " ".join(MORSE.get(c, '?') for c in w)
        for w in t.upper().split()
    )

def morse_decode(t):
    return ''.join(
        ' ' if x == '/' else MI.get(x, '?')
        for x in t.split()
    )

def phon_encode(t):
    return " / ".join(
        " ".join(PH.get(c, '?') for c in w)
        for w in t.upper().split()
    )

def phon_decode(t):
    return ''.join(
        ' ' if x == '/' else PHI.get(x.upper(), '?')
        for x in t.split()
    )

def square_encode(t):
    return ' '.join(
        '/' if c == ' ' else CI.get(c, '?')
        for c in t.upper()
    )

def square_decode(t):
    return ''.join(
        ' ' if x == '/' else CARRE.get(x, '?')
        for x in t.split()
    )

def hash_encode(t):
    return ' '.join(
        '/' if c == ' ' else HASH.get(c, '?')
        for c in t.upper()
    )

def hash_decode(t):
    return ''.join(
        ' ' if x == '/' else HI.get(x, '?')
        for x in t.split()
    )

st.title("⚜️ FAUCO CODE")
st.subheader("GÉNIE INFORMATIQUE")
st.caption("TOUJOURS PRÊT ! | Version 2.0")

st.divider()

code = st.selectbox("Choisir un système", [
    "MORSE",
    "K6 - CÉSAR +6",
    "PHONÉTIQUE",
    "CARRÉ 5x5",
    "CODE #"
])

mode = st.radio(
    "Opération",
    ["Coder", "Décoder"],
    horizontal=True
)

texte = st.text_area("Ton message", height=130)

fonctions = {
    ("MORSE","Coder"): morse_encode,
    ("MORSE","Décoder"): morse_decode,
    ("K6 - CÉSAR +6","Coder"): lambda t: cesar(t,6),
    ("K6 - CÉSAR +6","Décoder"): lambda t: cesar(t,-6),
    ("PHONÉTIQUE","Coder"): phon_encode,
    ("PHONÉTIQUE","Décoder"): phon_decode,
    ("CARRÉ 5x5","Coder"): square_encode,
    ("CARRÉ 5x5","Décoder"): square_decode,
    ("CODE #","Coder"): hash_encode,
    ("CODE #","Décoder"): hash_decode
}

if st.button("⚡ EXÉCUTER", use_container_width=True):
    if texte.strip():
        resultat = fonctions[(code,mode)](texte)
        st.session_state.resultat = resultat

        if "historique" not in st.session_state:
            st.session_state.historique = []

        st.session_state.historique.insert(0, {
            "code": code,
            "mode": mode,
            "resultat": resultat
        })

        st.success("Opération réussie !")
    else:
        st.warning("Entre un message.")

if "resultat" in st.session_state:
    st.subheader("📌 RÉSULTAT")
    st.code(st.session_state.resultat)

    st.button(
        "📋 Copier le résultat",
        on_click=lambda: st.write(
            "Sélectionne et copie le résultat ci-dessus."
        )
    )

st.divider()
st.subheader("📚 HISTORIQUE")

for item in st.session_state.get("historique",[])[:10]:
    with st.expander(item["code"]+" - "+item["mode"]):
        st.code(item["resultat"])

if st.button("Effacer l'historique"):
    st.session_state.historique = []
    st.rerun()

st.divider()
st.markdown("### ⚜️ FAUCO CODE")
st.caption("Créé par un futur ingénieur IESC")
st.caption("TOUJOURS PRÊT !")

