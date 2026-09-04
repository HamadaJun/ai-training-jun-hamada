from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from typing import Any, List, Optional

from dotenv import load_dotenv

def build_parser() -> argparse.ArgumentParser:
    """Day02のCLI引数を定義します（READMEの機能要件に対応）。"""
    p = argparse.ArgumentParser(prog="day02")
    p.add_argument("--prompt", required=True)
    p.add_argument("--region", default=None)
    p.add_argument("--model-id", default=None)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--timeout-sec", type=int, default=30)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.prompt:
        raise ValueError("--prompt is required")
    if not (0.0 <= args.temperature <= 1.0):
        raise ValueError("--temperature must be between 0.0 and 1.0")
    if args.max_tokens <= 0:
        raise ValueError("--max-tokens must be a positive integer")
    if args.timeout_sec <= 0:
        raise ValueError("--timeout-sec must be a positive integer")


def _extract_bedrock_text(payload: Any) -> str:
    """Bedrock APIのレスポンスから本文テキストを抽出します。"""
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected Bedrock response body: {type(payload).__name__}")

    if "content" in payload and isinstance(payload["content"], list):
        texts: List[str] = []
        for item in payload["content"]:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text:
                texts.append(text)
        if texts:
            return "".join(texts).strip()

    output = payload.get("output")
    if isinstance(output, dict):
        message = output.get("message", {})
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                texts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str) and text:
                            texts.append(text)
                if texts:
                    return "".join(texts).strip()

    completion = payload.get("completion")
    if isinstance(completion, str) and completion:
        return completion.strip()

    for key in ("answer", "text", "outputText"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value.strip()

    raise ValueError(
        "Unexpected Bedrock response format: "
        f"keys={sorted(payload.keys())[:10]}"
    )


def invoke_bedrock(
    *,
    prompt: str,
    region: str,
    model_id: str,
    temperature: float,
    max_tokens: int,
    timeout_sec: int,
) -> str:
    """Bedrockを呼び出して回答本文（文字列）を返します。"""
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required and cannot be empty")

    if not region:
        raise ValueError("region is required")
    if not model_id:
        raise ValueError("model-id is required")
    if not (0.0 <= temperature <= 1.0):
        raise ValueError("temperature must be between 0.0 and 1.0")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")
    if timeout_sec <= 0:
        raise ValueError("timeout_sec must be a positive integer")

    try:
        import boto3
        from botocore.config import Config
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "boto3 is required. Install it with: pip install boto3"
        ) from exc

    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(
                connect_timeout=timeout_sec,
                read_timeout=timeout_sec,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
    except Exception as exc:  # pragma: no cover - boto3 setup failure path
        raise RuntimeError(
            f"Failed to initialize Bedrock client for region={region}: {exc}"
        ) from exc

    if "anthropic.claude" in model_id:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        }
    else:
        payload = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "stopSequences": [],
            },
        }

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload).encode("utf-8"),
            accept="application/json",
            contentType="application/json",
        )
    except Exception as exc:
        message = str(exc)
        lower = message.lower()
        if "access denied" in lower or "not authorized" in lower or "unauthorized" in lower:
            raise PermissionError(
                f"AWS permission failed while calling Bedrock: {message}"
            ) from exc
        if "timed out" in lower or "timeout" in lower:
            raise TimeoutError(
                f"Bedrock request timed out after {timeout_sec}s: {message}"
            ) from exc
        if "unable to locate credentials" in lower or "credential" in lower:
            raise PermissionError(f"AWS authentication failed: {message}") from exc
        if "network" in lower or "connection" in lower or "temporary" in lower:
            raise ConnectionError(f"Bedrock network error: {message}") from exc
        raise RuntimeError(f"Bedrock invocation failed: {message}") from exc

    try:
        body = response.get("body")
        if body is None:
            raise ValueError("Bedrock response has no body")
        if hasattr(body, "read"):
            response_body = json.loads(body.read())
        else:
            response_body = json.loads(body)
    except Exception as exc:  # pragma: no cover - response parsing failure path
        raise ValueError(f"Failed to parse Bedrock response body: {exc}") from exc

    try:
        text = _extract_bedrock_text(response_body)
    except ValueError as exc:
        raise ValueError(
            f"Bedrock returned an unexpected response format for model={model_id}: {exc}"
        ) from exc

    if not text:
        raise ValueError("Bedrock returned an empty response body")

    return text


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は原則 `invoke_bedrock()` のみ実装し、それ以外は触らない想定です。
    """
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    region: Optional[str] = args.region or os.getenv("AWS_REGION")
    model_id: Optional[str] = args.model_id or os.getenv("BEDROCK_MODEL_ID")

    if not region:
        msg = "region is required: set --region or AWS_REGION"
        logging.error(msg)
        print(msg, file=sys.stderr)
        return 2

    if not model_id:
        msg = "model-id is required: set --model-id or BEDROCK_MODEL_ID"
        logging.error(msg)
        print(msg, file=sys.stderr)
        return 2

    logging.info(
        "region=%s model-id=%s temperature=%s max-tokens=%s timeout-sec=%s",
        region,
        model_id,
        args.temperature,
        args.max_tokens,
        args.timeout_sec,
    )

    try:
        reply = invoke_bedrock(
            prompt=args.prompt,
            region=region,
            model_id=model_id,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout_sec=args.timeout_sec,
        )
        print(reply)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
