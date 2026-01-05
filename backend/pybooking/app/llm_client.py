import os
import json
import asyncio
import traceback
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash"

def _compress_image(orig_bytes: bytes, max_width: int = 800, quality: int = 60) -> bytes:
    """
    Resize + compress image to keep payload small. Returns JPEG bytes.
    """

    try:
        img = Image.open(BytesIO(orig_bytes)).convert("RGB")
    except Exception:
        # If PIL can't open, return original bytes
        return orig_bytes

    w, h = img.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        img = img.resize((max_width, new_h), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=quality)
    return out.getvalue()

async def llm_stream(image_bytes_list: list[bytes], filenames: list[str] | None = None, context_text: str | None = None):
    """
    Async generator: yields parsed JSON event dicts from Gemini streaming output.
    """

    system_instruction = (
        "SYSTEM: You MUST output only newline-delimited JSON objects, one JSON per line. "
        "You MUST emit events in this exact order: extraction → comparison → final. "
        "The FINAL event is REQUIRED and MUST be the last event. "
        "Allowed event types: 'progress', 'extraction', 'comparison', 'final'. "

        "Extraction events schema: "
        "{ type:'extraction', payload:{ screenshot:{ screenshot_id, classification "
        "(initial_quote|final_booking|unknown), extraction:{ hotel_name, check_in, "
        "check_out, guests, total_price }}}}. "
        "Use the string 'unclear' for any field that is not confidently visible. "

        "Comparison events schema: "
        "{ type:'comparison', payload:{ field "
        "(hotel_name|check_in|check_out|guests|total_price), initial_value, final_value, "
        "status(match|mismatch|unclear), explanation, evidence:[screenshot_id] }}. "

        "Final event schema (REQUIRED): "
        "{ type:'final', payload:{ summary:{ overall(match|mismatch|unclear), detail }}}. "

        "Rules: "
        "• Emit one extraction event per screenshot immediately after processing it. "
        "• Emit exactly one comparison per field. "
        "• After ALL comparisons, emit EXACTLY ONE final event. "
        "• NEVER omit the final event. "
        "• NEVER output anything except valid JSON lines."
    )

    user_prompt = (
        "Task: Verify whether booking information in the final booking matches the initial quote. "

        "Process instructions: "
        "1) For EACH screenshot, emit one extraction event immediately. "
        "2) After all extractions, emit comparison events for these fields in order: "
        "hotel_name, check_in, check_out, guests, total_price. "
        "3) After ALL comparisons, you MUST emit one final event summarizing the result. "

        "Final event instructions: "
        "• overall = 'match' ONLY if ALL fields are 'match'. "
        "• overall = 'mismatch' if ANY field is 'mismatch'. "
        "• overall = 'unclear' otherwise. "
        "• detail must be a short human-readable summary explaining the decision. "

        "Output constraints: "
        "• Output ONLY newline-delimited JSON objects. "
        "• Do NOT explain your reasoning outside JSON. "
        "• Do NOT stop early. The final event is REQUIRED."
    )

    # Prepare contents (text + images). We'll compress, and if any image stays too large we'll abort with a clear event.
    contents = [
        types.Part.from_text(text=system_instruction),
        types.Part.from_text(text=user_prompt),
    ]
    MAX_SAFE_BYTES = 2_400_000  # 2.4 MB safe threshold

    # compress and attach images
    for idx, raw in enumerate(image_bytes_list):
        try:
            # first pass compress
            proc = _compress_image(raw, max_width=800, quality=60)
            # if still large, try stronger compression
            if len(proc) > MAX_SAFE_BYTES:
                proc = _compress_image(raw, max_width=600, quality=45)
            # final size check
            if len(proc) > MAX_SAFE_BYTES:
                raise ValueError(
                    f"Image {idx} (filename={filenames[idx] if filenames and idx < len(filenames) else idx}) "
                    f"is too large after compression ({len(proc)} bytes). Reduce resolution or remove."
                )
            # note: use keyword args for from_bytes
            contents.append(types.Part.from_bytes(data=proc, mime_type="image/jpeg"))
        except Exception as e:
            raise RuntimeError(f"Failed preparing image {idx}: {str(e)}") from e

        # label with filename so the model sees the file order
        sid = filenames[idx] if filenames and idx < len(filenames) else f"img_{idx+1}"
        contents.append(types.Part.from_text(text=f"SCREENSHOT_ID:{sid}"))

    if context_text:
        contents.append(types.Part.from_text(text=f"Context: {context_text}"))

    # Async queue + background thread runner
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def run_stream_and_enqueue():
        """
        Background thread: runs blocking genai streaming and enqueues dict events into asyncio queue.
        All exceptions are caught and enqueued as 'progress' events with tracebacks.
        """
        try:
            client = genai.Client()
        except Exception as e:
            payload = {"type": "progress", "payload": {"message": f"LLM error: {str(e)}", "error": str(e), "trace": traceback.format_exc()}}
            asyncio.run_coroutine_threadsafe(q.put(payload), loop)
            asyncio.run_coroutine_threadsafe(q.put({"type": "stream_end", "payload": {}}), loop)
            return

        buffer = ""
        try:
            try:
                stream = client.models.generate_content_stream(model=MODEL, contents=contents)
            except Exception as e:
                payload = {"type": "progress", "payload": {"message": "llm_start_error", "error": str(e), "trace": traceback.format_exc()}}
                asyncio.run_coroutine_threadsafe(q.put(payload), loop)
                asyncio.run_coroutine_threadsafe(q.put({"type": "stream_end", "payload": {}}), loop)
                return

            for chunk in stream:
                txt = getattr(chunk, "text", None) or ""
                if not txt:
                    continue
                buffer += txt
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line == "[DONE]":
                        continue
                    try:
                        ev = json.loads(line)
                        asyncio.run_coroutine_threadsafe(q.put(ev), loop)
                    except Exception:
                        pass

            # leftover buffer
            if buffer.strip():
                final_line = buffer.strip()
                try:
                    ev = json.loads(final_line)
                    asyncio.run_coroutine_threadsafe(q.put(ev), loop)
                except Exception:
                    pass

        except Exception as e:
            # enqueue exception trace
            asyncio.run_coroutine_threadsafe(q.put({"type": "progress", "payload": {"message": f"LLM stream error: {str(e.message)}", "error": str(e), "trace": traceback.format_exc()}}), loop)
        finally:
            asyncio.run_coroutine_threadsafe(q.put({"type": "stream_end", "payload": {}}), loop)

    # run the blocking streaming in a background thread
    thread_task = loop.run_in_executor(None, run_stream_and_enqueue)

    try:
        while True:
            ev = await q.get()
            if not isinstance(ev, dict):
                continue
            if ev.get("type") == "stream_end":
                break
            yield ev
    finally:
        await thread_task
