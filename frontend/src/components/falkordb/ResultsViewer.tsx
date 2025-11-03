/**
 * Displays query results and statistics
 */

import type { QueryResponse } from '../../types/falkordb';

interface ResultsViewerProps {
  result: QueryResponse | null;
}

export const ResultsViewer = ({ result }: ResultsViewerProps) => {
  if (!result) {
    return (
      <div className="results-viewer empty">
        <div className="empty-icon">📊</div>
        <p>Execute a query to see results</p>
      </div>
    );
  }

  return (
    <div className="results-viewer">
      <div className="results-header">
        <h3>Query Results</h3>
        <div className="results-stats">
          <span className="stat">
            <strong>{result.row_count}</strong> rows
          </span>
          <span className="stat">
            <strong>{result.execution_time_ms.toFixed(2)}</strong> ms
          </span>
        </div>
      </div>

      {result.results.length === 0 ? (
        <div className="empty-results">
          <p>No results found</p>
        </div>
      ) : (
        <div className="results-table-container">
          <table className="results-table">
            <thead>
              <tr>
                {Object.keys(result.results[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.results.map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((value, cellIdx) => (
                    <td key={cellIdx}>
                      {typeof value === 'object' ? (
                        <pre className="json-cell">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : (
                        String(value)
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result.message && (
        <div className="results-message success">
          ✓ {result.message}
        </div>
      )}
    </div>
  );
};

