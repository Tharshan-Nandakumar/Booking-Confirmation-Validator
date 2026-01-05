import "./FilePreview.css";

const FilePreview = ({ files = [], running, onStart, onClear }) => {
  return (
    <div>
      <div className="preview-container">
        <div>
          {files.length === 0 && (
            <div className="muted">No images selected</div>
          )}
          {files.length === 1 && (
            <div className="muted">At least two screenshots required</div>
          )}
        </div>
        <div className="preview-image-container">
          {files.map((file, i) => {
            const url = URL.createObjectURL(file);
            return (
              <div key={`${file.name}_${file.size}`} className="preview-card">
                <img src={url} alt={file.name} className="preview-img" />
                <div className="preview-caption">{file.name}</div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="controls">
        <button
          className="btn primary"
          onClick={onStart}
          disabled={running || files.length < 2}
        >
          Start Validation
        </button>
        <button className="btn" onClick={onClear} style={{ marginLeft: 8 }}>
          Clear / Cancel
        </button>
      </div>
    </div>
  );
};

export default FilePreview;
