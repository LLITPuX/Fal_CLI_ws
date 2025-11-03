/**
 * Form for executing Cypher queries
 */

import { useState } from 'react';
import type { QueryRequest } from '../../types/falkordb';

interface QueryFormProps {
  onExecute: (request: QueryRequest) => Promise<void>;
  isLoading: boolean;
}

const EXAMPLE_QUERIES = [
  'MATCH (n) RETURN n LIMIT 10',
  'MATCH (p:Person) RETURN p',
  'MATCH (p:Person)-[r]->(c:Company) RETURN p, r, c',
  'MATCH (n:Person {name: "John"}) RETURN n',
];

export const QueryForm = ({ onExecute, isLoading }: QueryFormProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      alert('Query is required');
      return;
    }

    await onExecute({
      query: query.trim(),
      params: {},
    });
  };

  const loadExample = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="falkordb-query-section">
      <h3>🔍 Execute Cypher Query</h3>

      <form onSubmit={handleSubmit} className="falkordb-form">
        <div className="form-group">
          <label htmlFor="cypher-query">Cypher Query *</label>
          <textarea
            id="cypher-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="MATCH (n) RETURN n LIMIT 10"
            rows={6}
            disabled={isLoading}
            required
            className="code-input"
          />
        </div>

        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? (
            <>
              <span className="spinner-small"></span> Executing...
            </>
          ) : (
            'Execute Query'
          )}
        </button>
      </form>

      <div className="example-queries">
        <h4>Example Queries:</h4>
        <div className="examples-list">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              onClick={() => loadExample(example)}
              className="example-button"
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

