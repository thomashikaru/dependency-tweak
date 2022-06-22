import streamlit as st
from spacy_streamlit import visualize_parser
import corpus_iterator
import corpus_iterator_funchead
from apply_counterfactual_grammar import orderSentence
import random

# set wide layout
st.set_page_config(layout="wide")

deps = [
    "acl",
    "advcl",
    "advmod",
    "amod",
    "appos",
    "aux",
    "case",
    "ccomp",
    "compound",
    "conj",
    "csubj",
    "det",
    "expl",
    "fixed",
    "flat",
    "iobj",
    "lifted_case",
    "lifted_cc",
    "lifted_cop",
    "lifted_mark",
    "nmod",
    "nsubj",
    "nummod",
    "obj",
    "obl",
    "parataxis",
    "punct",
    "xcomp",
]

N_DEPS = 28
N_COLS = 7

example = """1	The	the	DET	DEF	Definite=Def|PronType=Art	2	det	_	_
2	danger	danger	NOUN	SG-NOM	Number=Sing	8	nsubj	_	_
3	to	to	ADP	_	_	4	case	_	_
4	Germany	Germany	PROPN	SG-NOM	Number=Sing	2	nmod	_	_
5	from	from	ADP	_	_	7	case	_	_
6	the	the	DET	DEF	Definite=Def|PronType=Art	7	det	_	_
7	Hussites	Hussites	NOUN	PL-NOM	Number=Plur	2	nmod	_	_
8	induced	induce	VERB	PAST	Mood=Ind|Tense=Past|VerbForm=Fin	0	root	_	_
9	Frederick	Frederick	PROPN	SG-NOM	Number=Sing	8	obj	_	_
10	to	to	PART	_	_	11	mark	_	_
11	ally	ally	VERB	INF	VerbForm=Inf	8	advcl	_	_
12	himself	he	PRON	RFL-P3SG	Case=Acc|Gender=Masc|Number=Sing|Person=3|PronType=Prs|Reflex=Yes	11	obj	_	_
13	with	with	ADP	_	_	15	case	_	_
14	Emperor	Emperor	ADJ	POS	Degree=Pos	15	amod	_	_
15	Sigismund	Sigismund	NOUN	SG-NOM	Number=Sing	11	obl	_	_
16	;	;	PUNCT	SemiColon	_	8	punct	_	_"""

# convert sentence from Michael's format to displaCy render (manual) format
def convert_sentence(sentence):
    words, arcs = [], []
    for word in sentence:
        words.append({"text": word["word"], "tag": word["posUni"]})
        idx, head = int(word["index"]), int(word["reordered_head"])
        if head == 0:
            continue
        dir = "right"
        if idx > head:
            idx, head = head, idx
            dir = "left"
        arcs.append(
            {"start": idx - 1, "end": head - 1, "label": word["dep"], "dir": dir,}
        )
    return {"words": words, "arcs": arcs}


# initialize random weights for dh and distance weights
@st.cache(allow_output_mutation=True)
def initialize_weights():
    dh_weights, distance_weights = {}, {}
    for x in deps:
        dh_weights[x] = random.random() - 0.5
        distance_weights[x] = random.random() - 0.5
    return dh_weights, distance_weights


dh_weights, distance_weights = initialize_weights()

# page title
st.title("Counterfactual Grammar Visualization")

# input original parse (includes default example)
st.header("Original Parse")
text = st.text_area("Enter text in CoNLL format:", value=example, height=400)
text = text.strip()

# get the sentence
corpus = corpus_iterator.CorpusIterator("", "English")
sentence, newdoc = corpus.processSentence(text)
sentence = corpus_iterator_funchead.reverse_content_head(sentence)

# where to display parse tree (create it but populate it later, after sliders)
treebox = st.container()

# sliders for dh weights
st.header("Dependent-Head Weights")
st.caption(
    "A positive weight for a given relation means that the dependent will occur before the head in linear order."
)
dhcols = st.columns(N_COLS)
for i, dhcol in enumerate(dhcols):
    with dhcol:
        slider_vals = {}
        for dep in deps[N_DEPS * i // N_COLS : N_DEPS * (i + 1) // N_COLS]:
            if dep in dh_weights:
                dh_weights[dep] = st.slider(
                    dep, -1.0, 1.0, dh_weights[dep], key="dh" + dep
                )

# sliders for distance weights
st.header("Distance Weights")
st.caption(
    "For dependents on the same side of a head, those with higher weights will be placed farther from the head in linear order."
)
distcols = st.columns(N_COLS)
for i, distcol in enumerate(distcols):
    with distcol:
        slider_vals = {}
        for dep in deps[N_DEPS * i // N_COLS : N_DEPS * (i + 1) // N_COLS]:
            if dep in distance_weights:
                distance_weights[dep] = st.slider(
                    dep, -1.0, 1.0, distance_weights[dep], key="dist" + dep
                )

# update the treebox
with treebox:
    sentence = orderSentence(sentence, "RANDOM", dh_weights, distance_weights)
    for i, s in enumerate(sentence):
        s["index"] = i + 1
    data = convert_sentence(sentence)
    visualize_parser(data, manual=True)
