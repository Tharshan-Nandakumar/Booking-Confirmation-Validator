import "./StreamResults.css";

const Badge = ({ status }) => {
  if (!status) return null;
  if (status === "match") return <span className="badge match">match</span>;
  if (status === "mismatch")
    return <span className="badge mismatch">mismatch</span>;
  return <span className="badge unclear">unclear</span>;
};

const StreamResults = ({ logs = [], comparisons = [] }) => {
  return (
    <div className="card">
      <h3>Streaming log</h3>

      <div className="stream-log">
        {logs.length === 0 ? (
          <div className="muted">No events yet</div>
        ) : (
          logs.map((log, i) => (
            <div
              key={i}
              className="log-row"
              style={{ color: log.text.includes("error") ? "red" : "" }}
            >
              <div className="log-time">{new Date().toLocaleTimeString()}</div>
              <div className="log-text">{log.text}</div>
            </div>
          ))
        )}
      </div>

      <h3>Results</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Initial</th>
            <th>Final</th>
            <th>Status</th>
            <th>Explanation</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {comparisons.length === 0 ? (
            <tr>
              <td colSpan={6}>No comparisons yet.</td>
            </tr>
          ) : (
            comparisons.map((c, i) => (
              <tr key={`${c.field}_${i}`}>
                <td>{c.field}</td>
                <td>{c.initial_value ?? "unclear"}</td>
                <td>{c.final_value ?? "unclear"}</td>
                <td>
                  <Badge status={c.status} />
                </td>
                <td>{c.explanation ?? ""}</td>
                <td>
                  {(c.evidence || []).length
                    ? (c.evidence || []).join(", ")
                    : "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default StreamResults;
