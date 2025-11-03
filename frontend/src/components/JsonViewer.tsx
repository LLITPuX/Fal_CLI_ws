import type { MultiModelResponse, ModelResult } from '../types/api';

interface JsonViewerProps {
  data: MultiModelResponse;
}

const ModelResultCard: React.FC<{ result: ModelResult; index: number }> = ({ result, index }) => {
  const copyToClipboard = async () => {
    if (!result.data) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(result.data, null, 2));
      alert(`Copied ${result.metrics?.model} result to clipboard!`);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadJson = () => {
    if (!result.data) return;
    const blob = new Blob([JSON.stringify(result.data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.id}_${result.metrics?.model}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (result.error) {
    return (
      <div className="model-result error-result">
        <div className="model-header">
          <h3 className="model-name">{result.metrics?.model || `Model ${index + 1}`}</h3>
          <span className="error-badge">❌ Failed</span>
        </div>
        <div className="error-message">
          <p>{result.error}</p>
        </div>
      </div>
    );
  }

  if (!result.data || !result.metrics) {
    return null;
  }

  return (
    <div className="model-result">
      <div className="model-header">
        <h3 className="model-name">{result.metrics.model}</h3>
        <div className="actions">
          <button onClick={copyToClipboard} className="action-btn" title="Copy to clipboard">
            📋 Copy
          </button>
          <button onClick={downloadJson} className="action-btn" title="Download JSON">
            💾 Download
          </button>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric">
          <span className="metric-label">⏱️ Processing Time</span>
          <span className="metric-value">{result.metrics.processing_time_seconds}s</span>
        </div>
        <div className="metric">
          <span className="metric-label">📥 Input</span>
          <span className="metric-value">
            {result.metrics.input_characters.toLocaleString()} chars
            <span className="metric-sub">
              (~{result.metrics.input_tokens_estimate.toLocaleString()} tokens)
            </span>
          </span>
        </div>
        <div className="metric">
          <span className="metric-label">📤 Output</span>
          <span className="metric-value">
            {result.metrics.output_characters.toLocaleString()} chars
            <span className="metric-sub">
              (~{result.metrics.output_tokens_estimate.toLocaleString()} tokens)
            </span>
          </span>
        </div>
      </div>

      <div className="result-info">
        <span className="info-item">
          <strong>ID:</strong> {result.id}
        </span>
        <span className="info-item">
          <strong>Saved:</strong> {result.json_path}
        </span>
      </div>

      <div className="data-preview">
        {'title' in result.data && 'summary' in result.data ? (
          <>
            <div className="preview-card">
              <h4>{result.data.title}</h4>
              <p className="date">{result.data.date_iso}</p>
              <p className="summary">{result.data.summary}</p>
              <div className="tags">
                {result.data.tags?.map((tag: string, idx: number) => (
                  <span key={idx} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="sections">
              <h5>Sections ({result.data.sections?.length || 0})</h5>
              {result.data.sections?.map((section: any, idx: number) => (
                <details key={idx} className="section" open={idx === 0}>
                  <summary>{section.name}</summary>
                  <p>{section.content}</p>
                </details>
              ))}
            </div>
          </>
        ) : (
          <div className="custom-schema-preview">
            <h5>Користувацька структура</h5>
            <p className="hint">Дані відповідають вашій схемі. Перегляньте повний JSON нижче.</p>
          </div>
        )}
      </div>

      <details className="raw-json">
        <summary>Raw JSON</summary>
        <pre>
          <code>{JSON.stringify(result.data, null, 2)}</code>
        </pre>
      </details>
    </div>
  );
};

export const JsonViewer: React.FC<JsonViewerProps> = ({ data }) => {
  const failedResults = data.results.filter((r) => r.error);

  return (
    <div className="json-viewer">
      <div className="viewer-header">
        <h3>✨ Structured Results</h3>
        <div className="summary-stats">
          {failedResults.length > 0 && (
            <span className="stat error">❌ {failedResults.length} failed</span>
          )}
          <span className="stat">⏱️ Time: {data.total_processing_time_seconds}s</span>
        </div>
      </div>

      <div className="models-comparison">
        {data.results.map((result, index) => (
          <ModelResultCard key={index} result={result} index={index} />
        ))}
      </div>
    </div>
  );
};

