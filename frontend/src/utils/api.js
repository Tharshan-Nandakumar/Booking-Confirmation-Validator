export const startStreamUpload = async (files, context, onEvent) => {
  const form = new FormData();
  for (const f of files) form.append("files", f, f.name);
  if (context) form.append("context", context);

  const resp = await fetch(`${process.env.REACT_APP_BACKEND_URL}/stream`, {
    method: "POST",
    body: form,
  });
  if (!resp.body) throw new Error("Server returned no body");

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  const chunkSSEBuffer = (buf) => {
    const parts = buf.split("\n\n");
    if (parts.length === 0) return [[], ""];
    const rest = parts.pop();
    return [parts, rest];
  };
  const parseSSEMessage = (msg) => {
    const lines = msg
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    const dataLines = lines.filter((l) => l.startsWith("data:"));
    return dataLines.map((l) => l.slice(5).trim());
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const [messages, rest] = chunkSSEBuffer(buf);
    buf = rest;
    for (const m of messages) {
      const pieces = parseSSEMessage(m);
      for (const p of pieces) {
        try {
          const ev = JSON.parse(p);
          if (onEvent) onEvent(ev);
        } catch (err) {
          if (onEvent)
            onEvent({
              type: "progress",
              payload: { message: "json_parse_error", raw: p },
            });
        }
      }
    }
  }
};
