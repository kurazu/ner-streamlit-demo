import email
import email.message
import email.policy
import random
import zipfile
from pathlib import Path
from typing import cast

import en_core_web_trf
import streamlit as st
from spacy import displacy
from spacy.language import Language


@st.experimental_singleton
def get_nlp() -> Language:
    return en_core_web_trf.load()


def get_zipfile() -> zipfile.ZipFile:
    here = Path(__file__).parent
    zipfile_path = here / "EnronMeetings-XML.zip"
    return zipfile.ZipFile(zipfile_path, "r")


@st.experimental_singleton
def get_all_filepaths() -> list[str]:
    with get_zipfile() as zf:
        filenames = zf.namelist()
    return [filename for filename in filenames if filename.endswith(".txt")]


def _get_email_body(
    msg: email.message.EmailMessage, default_encoding="us-ascii"
) -> tuple[str, str]:
    sub_msg = msg.get_body(preferencelist=("plain",))
    assert sub_msg is not None
    assert not sub_msg.is_multipart()
    (charset,) = sub_msg.get_charsets(failobj=default_encoding)
    if charset == "ansi":
        charset = default_encoding
    data = sub_msg.get_payload(decode=True)
    subject = sub_msg.get("subject")
    decoded_data = data.decode(charset, errors="replace")
    return subject, decoded_data


def get_email_body(path: Path) -> tuple[str, str]:
    with path.open("rb") as f:
        msg = cast(
            email.message.EmailMessage,
            email.message_from_binary_file(f, policy=email.policy.default),
        )
    return _get_email_body(msg)


START_TAG = "<true_name>"
END_TAG = "</true_name>"


def remove_tags(text: str) -> str:
    return text.replace(START_TAG, "").replace(END_TAG, "")


st.markdown("# NER Demo")

nlp = get_nlp()

random_file_path = random.choice(get_all_filepaths())
with get_zipfile() as zf:
    with zf.open(random_file_path, "r") as f:
        msg = cast(
            email.message.EmailMessage,
            email.message_from_binary_file(f, policy=email.policy.default),
        )
        default_subject, default_body = map(remove_tags, _get_email_body(msg))


def process_ner(text: str) -> None:
    doc = nlp(text)
    html = displacy.render(doc, style="ent", minify=True)

    with st.container():
        st.write(html, unsafe_allow_html=True)


st.markdown("## Input email subject")

subject = st.text_input(label="Email subject", value=default_subject)

st.markdown("## Input email body")

body = st.text_area(label="Email body", value=default_body, height=300)

st.markdown("## Processed email subject")

process_ner(subject)

st.markdown("## Processed email body")

process_ner(body)
