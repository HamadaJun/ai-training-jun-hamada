from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st

from final.agent import run_agent


st.set_page_config(page_title="AI Agent Chat", layout="centered")

st.title("AI Agent Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("meta") is not None:
            with st.expander("meta"):
                st.code(json.dumps(m["meta"], ensure_ascii=False, indent=2), language="json")

prompt = st.chat_input("Type a message")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant")
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result: Dict[str, Any] = run_agent(prompt, history=history)
            reply = str(result.get("reply", ""))
            meta = result.get("meta")

        st.markdown(reply)
        if meta is not None:
            with st.expander("meta"):
                st.code(json.dumps(meta, ensure_ascii=False, indent=2), language="json")

    st.session_state.messages.append({"role": "assistant", "content": reply, "meta": meta})
