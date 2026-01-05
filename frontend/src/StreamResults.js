const Badge = ({ status }) => {
  if (!status) return null;
  if (status === "match") return <span className="badge-match">match</span>;
  if (status === "mismatch")
    return <span className="badge-mismatch">mismatch</span>;
  return <span className="badge-unclear">unclear</span>;
};

const StreamResults = ({ log, extractions, comparisons }) => {
  return (
    <div style={{ marginTop: 20 }}>
      <h3>Stream Log</h3>
      <div className="stream-log">
        {log.length === 0 && <div style={{ color: "#666" }}>No events yet</div>}
        {log.map((l, i) => (
          <div key={i}>
            <strong>{l.time}</strong> — {l.text}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 16, marginTop: 20 }}>
        <div style={{ flex: 1 }}>
          <h3>Extractions</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Screenshot</th>
                <th>Class</th>
                <th>Hotel</th>
                <th>Check-in</th>
                <th>Check-out</th>
                <th>Guests</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {extractions.length === 0 && (
                <tr>
                  <td colSpan={7}>No extractions yet.</td>
                </tr>
              )}
              {extractions.map((s, i) => (
                <tr key={i}>
                  <td>{s?.screenshot_id}</td>
                  <td>{s?.classification}</td>
                  <td>{s.extraction.hotel_name ?? "unclear"}</td>
                  <td>{s.extraction.check_in ?? "unclear"}</td>
                  <td>{s.extraction.check_out ?? "unclear"}</td>
                  <td>{s.extraction.guests ?? "unclear"}</td>
                  <td>{s.extraction.total_price ?? "unclear"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ flex: 1 }}>
          <h3>Comparisons</h3>
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
              {comparisons.length === 0 && (
                <tr>
                  <td colSpan={6}>No comparisons yet.</td>
                </tr>
              )}
              {comparisons.map((c, i) => (
                <tr key={i}>
                  <td>{c.field}</td>
                  <td>{c.initial_value}</td>
                  <td>{c.final_value}</td>
                  <td>
                    <Badge status={c.status} />
                  </td>
                  <td>{c.explanation}</td>
                  <td>{(c.evidence || []).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StreamResults;
