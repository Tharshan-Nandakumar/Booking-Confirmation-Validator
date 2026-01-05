import { useRef } from "react";
import "./UploadArea.css";

const UploadArea = ({ onFilesSelected, context, setContext }) => {
  const inputRef = useRef();

  const handleChange = (e) => {
    const files = e.target.files;
    if (!files) return;
    const arr = Array.from(files);
    e.target.value = "";
    onFilesSelected(arr);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (!files) return;
    onFilesSelected(Array.from(files));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <>
      <div
        className="upload-area"
        onClick={() => inputRef.current.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <div className="title">Upload or Drag & Drop booking screenshots</div>
        <div>Size up to 5MB</div>
        <div>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={handleChange}
            className="file-input"
          />
        </div>
      </div>
      <textarea
        value={context}
        onChange={(e) => setContext(e.target.value)}
        className="context-input"
        placeholder="Optional context for booking information"
      />
    </>
  );
};

export default UploadArea;
