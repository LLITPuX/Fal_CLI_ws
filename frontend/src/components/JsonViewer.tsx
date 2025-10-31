import type { StructureResponse } from '../types/api';

interface JsonViewerProps {
  data: StructureResponse;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({ data }) => {
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data.data, null, 2));
      alert('Copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(data.data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="json-viewer">
      <div className="viewer-header">
        <h3>Structured Result</h3>
        <div className="actions">
          <button onClick={copyToClipboard} className="action-btn" title="Copy to clipboard">
            📋 Copy
          </button>
          <button onClick={downloadJson} className="action-btn" title="Download JSON">
            💾 Download
          </button>
        </div>
      </div>

      <div className="result-info">
        <span className="info-item">
          <strong>ID:</strong> {data.id}
        </span>
        <span className="info-item">
          <strong>Saved to:</strong> {data.json_path}
        </span>
      </div>

      <div className="data-preview">
        <div className="preview-card">
          <h4>{data.data.title}</h4>
          <p className="date">{data.data.date_iso}</p>
          <p className="summary">{data.data.summary}</p>
          <div className="tags">
            {data.data.tags.map((tag, idx) => (
              <span key={idx} className="tag">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="sections">
          <h5>Sections ({data.data.sections.length})</h5>
          {data.data.sections.map((section, idx) => (
            <details key={idx} className="section" open={idx === 0}>
              <summary>{section.name}</summary>
              <p>{section.content}</p>
            </details>
          ))}
        </div>
      </div>

      <details className="raw-json">
        <summary>Raw JSON</summary>
        <pre>
          <code>{JSON.stringify(data.data, null, 2)}</code>
        </pre>
      </details>
    </div>
  );
};

