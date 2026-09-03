from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

import streamlit as st


@dataclass(frozen=True)
class RunResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


def run_command(command: List[str], timeout_sec: int = 30) -> RunResult:
    p = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    return RunResult(
        command=command,
        returncode=p.returncode,
        stdout=p.stdout,
        stderr=p.stderr,
    )


def render_result(result: RunResult) -> None:
    st.markdown("### 実行コマンド")
    st.code(" ".join(shlex.quote(x) for x in result.command), language="bash")

    cols = st.columns(3)
    cols[0].metric("exit code", result.returncode)
    cols[1].metric("stdout bytes", len(result.stdout.encode("utf-8")))
    cols[2].metric("stderr bytes", len(result.stderr.encode("utf-8")))

    st.markdown("### stdout")
    st.code(result.stdout or "(empty)")
    st.markdown("### stderr")
    st.code(result.stderr or "(empty)")


def app_day01() -> Tuple[List[str], int]:
    st.subheader("Day01: CLI 基礎")
    name = st.text_input("--name", value="Taro")
    repeat = st.number_input("--repeat", min_value=1, max_value=10, value=2, step=1)
    fmt = st.selectbox("--format", options=["text", "json"], index=0)
    timeout = st.number_input("timeout(sec)", min_value=1, max_value=120, value=20, step=1)

    cmd = ["python", "-m", "day01.app", "--name", name, "--repeat", str(int(repeat)), "--format", fmt]
    return cmd, int(timeout)


def app_day02() -> Tuple[List[str], int]:
    st.subheader("Day02: Bedrock Invoke")
    prompt = st.text_area("--prompt", value="Hello")
    region = st.text_input("--region (optional)", value="")
    model_id = st.text_input("--model-id (optional)", value="")
    temperature = st.number_input("--temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
    max_tokens = st.number_input("--max-tokens", min_value=1, max_value=4096, value=128, step=1)
    timeout = st.number_input("--timeout-sec", min_value=1, max_value=120, value=30, step=1)

    cmd = [
        "python",
        "-m",
        "day02.app",
        "--prompt",
        prompt,
        "--temperature",
        str(float(temperature)),
        "--max-tokens",
        str(int(max_tokens)),
        "--timeout-sec",
        str(int(timeout)),
    ]
    if region:
        cmd += ["--region", region]
    if model_id:
        cmd += ["--model-id", model_id]
    return cmd, int(timeout)


def app_day03() -> Tuple[List[str], int]:
    st.subheader("Day03: JSON 構造化")
    requirements = st.text_area("--requirements", value="Webページの問い合わせフォームを作りたい")
    max_retry = st.number_input("--max-retry", min_value=0, max_value=3, value=1, step=1)
    timeout = st.number_input("timeout(sec)", min_value=1, max_value=120, value=30, step=1)

    cmd = [
        "python",
        "-m",
        "day03.app",
        "--requirements",
        requirements,
        "--max-retry",
        str(int(max_retry)),
    ]
    return cmd, int(timeout)


def app_day04() -> Tuple[List[str], int]:
    st.subheader("Day04: LangChain + Tool")
    text = st.text_area("--text", value="今日の日付を教えて")
    timeout = st.number_input("timeout(sec)", min_value=1, max_value=120, value=30, step=1)

    cmd = ["python", "-m", "day04.app", "--text", text]
    return cmd, int(timeout)


def app_day05() -> Tuple[List[str], int]:
    st.subheader("Day05: RAG")
    question = st.text_area("--question", value="このデータの要点は？")
    timeout = st.number_input("timeout(sec)", min_value=1, max_value=120, value=30, step=1)

    cmd = ["python", "-m", "day05.app", "--question", question]
    return cmd, int(timeout)


def app_final_chat() -> Optional[str]:
    st.subheader("Final: Chat UI")
    st.markdown("StreamlitのチャットUIは別プロセスで起動します。")
    st.code("streamlit run final/chat_ui.py", language="bash")
    st.markdown("このダッシュボードからは起動しません（プロセス管理を単純にするため）。")
    return None


PAGES = {
    "Day01": app_day01,
    "Day02": app_day02,
    "Day03": app_day03,
    "Day04": app_day04,
    "Day05": app_day05,
    "Final (Chat UI)": app_final_chat,
}


st.set_page_config(page_title="Training Dashboard", layout="centered")
st.title("研修ダッシュボード")
st.caption("各DayのCLIを共通画面から実行し、stdout/stderr/exit code を確認します。")

page = st.sidebar.selectbox("メニュー", options=list(PAGES.keys()))

builder = PAGES[page]

if builder is app_final_chat:
    builder()
    st.stop()

cmd, timeout_sec = builder()

run = st.button("実行")

if run:
    try:
        result = run_command(cmd, timeout_sec=timeout_sec)
        render_result(result)
    except subprocess.TimeoutExpired:
        st.error(f"Timeout: {timeout_sec} seconds")
    except FileNotFoundError as e:
        st.error(f"Command not found: {e}")
    except Exception as e:
        st.exception(e)
