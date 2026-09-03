# backend

このディレクトリは「課題ランナーAPI」です。

- `POST /run` で `python -m <module> ...` を実行し、stdout/stderr/exit code を返します。
- UI（`ui/app.py`）がこのAPIを呼び出します。
