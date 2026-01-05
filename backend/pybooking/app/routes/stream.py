import json
import uuid
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from app.llm_client import llm_stream
from app.compare_fields import compare_fields
from app.models.models import MatchStatus, StreamEvent, ScreenshotResult


router = APIRouter(
    prefix="/stream"
)


def serialize_event(event_type: str, payload: dict) -> bytes:
    """
    Serializes an SSE event.
    """

    return f"data: {json.dumps({'type': event_type, 'payload': payload}, default=str)}\n\n".encode(
        "utf-8"
    )


@router.post("")
async def stream_endpoint(
    files: list[UploadFile] = File(...),
    context: str | None = Form(None),
):
    """
    Streams extraction, comparison, and final validation results
    for uploaded booking screenshots.
    """

    async def event_generator() -> AsyncGenerator[bytes, None]:
        image_bytes: list[bytes] = []
        filenames: list[str] = []

        # --- Read uploaded files ---
        for file in files:
            try:
                content = await file.read()
                image_bytes.append(content)
                filenames.append(file.filename or str(uuid.uuid4()))
            except Exception as exc:
                yield serialize_event(
                    "progress",
                    {
                        "message": f"file_read_error: {file.filename}",
                        "error": str(exc),
                        "trace": traceback.format_exc(),
                    },
                )

        if not image_bytes:
            yield serialize_event(
                "progress",
                {"message": "no_images_received"},
            )
            return

        screenshots: list[ScreenshotResult] = []
        model_emitted_comparisons = False
        model_emitted_final = False

        # --- Stream from LLM ---
        try:
            async for raw_event in llm_stream(image_bytes, filenames, context):
                if not isinstance(raw_event, dict):
                    yield serialize_event(
                        "progress",
                        {"message": "invalid_event_format", "raw": raw_event},
                    )
                    continue

                # Normalize Gemini-style payloads
                if "type" not in raw_event and "event_type" in raw_event:
                    raw_event["type"] = raw_event.pop("event_type")

                event_type = raw_event.get("type")
                if not event_type:
                    yield serialize_event(
                        "progress",
                        {"message": "missing_event_type", "raw": raw_event},
                    )
                    continue

                # Forward progress/debug events verbatim
                if event_type == "progress":
                    yield serialize_event(
                        "progress",
                        raw_event.get("payload", {"message": "progress"}),
                    )
                    continue

                # Validate structured events
                try:
                    StreamEvent.model_validate(raw_event)
                except Exception as exc:
                    yield serialize_event(
                        "progress",
                        {
                            "message": "invalid_event_skipped",
                            "error": str(exc),
                            "raw": raw_event,
                            "trace": traceback.format_exc(),
                        },
                    )
                    continue

                yield serialize_event(event_type, raw_event["payload"])

                if event_type == "comparison":
                    model_emitted_comparisons = True
                elif event_type == "final":
                    model_emitted_final = True
                elif event_type == "extraction":
                    try:
                        screenshot = ScreenshotResult.model_validate(
                            raw_event["payload"]["screenshot"]
                        )
                        screenshots.append(screenshot)
                    except Exception:
                        pass

        except Exception as exc:
            yield serialize_event(
                "progress",
                {
                    "message": f"llm_stream_error: {str(exc)}",
                    "error": str(exc),
                    "trace": traceback.format_exc(),
                },
            )

        # --- Server-side comparison fallback ---
        comparisons = None
        if not model_emitted_comparisons and screenshots:
            try:
                comparisons = compare_fields(screenshots)
                for comp in comparisons:
                    yield serialize_event(
                        "comparison",
                        comp.model_dump(),
                    )
            except Exception as exc:
                yield serialize_event(
                    "progress",
                    {
                        "message": "comparison_error",
                        "error": str(exc),
                        "trace": traceback.format_exc(),
                    },
                )

        # --- Final summary ---
        if not model_emitted_final:
            try:
                if comparisons is None and screenshots:
                    comparisons = compare_fields(screenshots)
                if comparisons:
                    matches = sum(c.status == MatchStatus.MATCH for c in comparisons)
                    mismatches = sum(c.status == MatchStatus.MISMATCH for c in comparisons)
                    unclears = sum(c.status == MatchStatus.UNCLEAR for c in comparisons)

                    overall = (
                        "match"
                        if mismatches == 0 and unclears == 0 and matches > 0
                        else "mismatch"
                        if mismatches > 0
                        else "unclear"
                    )

                    detail = (
                        f"{matches} match, "
                        f"{mismatches} mismatch, "
                        f"{unclears} unclear"
                    )
                else:
                    overall = "unclear"
                    detail = "no comparison data"
                yield serialize_event(
                    "final",
                    {"summary": {"overall": overall, "detail": detail}},
                )

            except Exception as exc:
                yield serialize_event(
                    "progress",
                    {
                        "message": f"final_summary_error: {str(exc)}",
                        "error": str(exc),
                        "trace": traceback.format_exc(),
                    },
                )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
