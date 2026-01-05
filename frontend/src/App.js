import { useState } from "react";
import UploadArea from "./components/uploadArea/UploadArea";
import FilePreview from "./components/filePreview/FilePreview";
import StreamResults from "./components/streamResults/StreamResults";
import { startStreamUpload } from "./utils/api";
import "./App.css";

const App = () => {
  const [files, setFiles] = useState([]);
  const [context, setContext] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  const [streamState, setStreamState] = useState({
    logs: [],
    comparisons: [],
  });

  const onFilesSelected = (fileArray) => {
    if (!fileArray || fileArray.length === 0) return;
    const arr = Array.from(fileArray);
    // basic validation: image types, <5MB each
    const filtered = arr.filter(
      (f) => f.type.startsWith("image/") && f.size <= 5 * 1024 * 1024
    );
    setFiles((prev) => {
      const map = new Map();
      prev.concat(filtered).forEach((f) => map.set(`${f.name}_${f.size}`, f));
      return Array.from(map.values());
    });
  };

  const clearAll = () => {
    setFiles([]);
    setContext("");
    setRunning(false);
    setStreamState({ logs: [], comparisons: [] });
    setResult(null);
  };

  const onStart = async () => {
    if (files.length === 0) {
      setStreamState((s) => ({
        ...s,
        logs: [
          ...s.logs,
          { level: "warn", text: "Select at least one image." },
        ],
      }));
      return;
    }

    setRunning(true);
    setStreamState({
      logs: [
        { level: "info", text: "Uploading images and starting processing..." },
      ],
      comparisons: [],
    });

    // callback invoked for each SSE event
    const onEvent = (ev) => {
      if (!ev || !ev.type) return;
      if (ev.type === "progress") {
        setStreamState((s) => ({
          ...s,
          logs: [
            ...s.logs,
            {
              level: "info",
              text: ev.payload.message ?? JSON.stringify(ev.payload),
            },
          ],
        }));
      }
      if (ev.type === "comparison") {
        setStreamState((s) => ({
          ...s,
          comparisons: [...s.comparisons, ev.payload],
          logs: [
            ...s.logs,
            {
              level: "info",
              text: `Comparison: ${ev.payload.field} => ${ev.payload.status}`,
            },
          ],
        }));
      }
      if (ev.type === "final") {
        const final = ev.payload.summary.overall.toUpperCase();
        setResult(final);
        setStreamState((s) => ({
          ...s,
          logs: [
            ...s.logs,
            {
              level: "success",
              text: `Final: ${final}`,
            },
          ],
        }));
        setRunning(false);
      }
    };

    try {
      await startStreamUpload(files, context, onEvent);
    } catch (err) {
      setStreamState((s) => ({
        ...s,
        logs: [
          ...s.logs,
          { level: "error", text: err?.message ?? String(err) },
        ],
      }));
      setRunning(false);
    }
  };

  const finalResultMap = {
    MATCH: { color: "green", text: "Initial quote and booking match!" },
    MISMATCH: { color: "red", text: "Initial quote and booking do not match" },
    UNCLEAR: {
      color: "#aaa",
      text: "Unable to determine if initial quote and booking match",
    },
  };

  return (
    <div className="app">
      <h1 className="header">Booking Confirmation Validator</h1>
      {!process.env.REACT_APP_BACKEND_URL && (
        <h4 className="error">
          REACT_APP_BACKEND_URL environment variable in not defined
        </h4>
      )}

      {finalResultMap[result] && (
        <h3
          style={{ color: finalResultMap[result].color, textAlign: "center" }}
        >
          {finalResultMap[result].text}
        </h3>
      )}

      <main className="container">
        <section className="card">
          <UploadArea
            onFilesSelected={onFilesSelected}
            context={context}
            setContext={setContext}
          />
          <FilePreview
            files={files}
            running={running}
            onStart={onStart}
            onClear={clearAll}
          />
        </section>

        <section>
          <StreamResults {...streamState} />
        </section>
      </main>
    </div>
  );
};

export default App;
