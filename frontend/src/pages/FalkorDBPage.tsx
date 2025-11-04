/**
 * FalkorDB Graph Database Page
 */

import { useState } from 'react';
import { NodeTemplateForm } from '../components/falkordb/NodeTemplateForm';
import { RelationshipForm } from '../components/falkordb/RelationshipForm';
import { QueryForm } from '../components/falkordb/QueryForm';
import { ResultsViewer } from '../components/falkordb/ResultsViewer';
import { GraphStatsCard } from '../components/falkordb/GraphStatsCard';
import { TemplateManager } from '../components/falkordb/TemplateManager';
import { falkorDBApi } from '../services/falkordb-api';
import type {
  CreateNodeRequest,
  CreateRelationshipRequest,
  QueryRequest,
  QueryResponse,
  FalkorDBState,
} from '../types/falkordb';
import '../styles/FalkorDB.css';

type ActiveTab = 'node' | 'relationship' | 'query' | 'templates';

export const FalkorDBPage = () => {
  const [state, setState] = useState<FalkorDBState>({ status: 'idle' });
  const [activeTab, setActiveTab] = useState<ActiveTab>('query');
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [statsKey, setStatsKey] = useState(0); // For forcing stats refresh
  const [availableLabels, setAvailableLabels] = useState<string[]>([]);
  const [availableRelationshipTypes, setAvailableRelationshipTypes] = useState<string[]>([]);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
    // Refresh stats
    setStatsKey((prev) => prev + 1);
  };

  const handleCreateNode = async (request: CreateNodeRequest) => {
    setState({ status: 'loading' });
    try {
      const response = await falkorDBApi.createNode(request);
      setState({ status: 'success', data: response });
      showSuccess(response.message);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create node';
      setState({ status: 'error', error: message });
    }
  };

  const handleCreateRelationship = async (request: CreateRelationshipRequest) => {
    setState({ status: 'loading' });
    try {
      const response = await falkorDBApi.createRelationship(request);
      setState({ status: 'success', data: response });
      showSuccess(response.message);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create relationship';
      setState({ status: 'error', error: message });
    }
  };

  const handleExecuteQuery = async (request: QueryRequest) => {
    setState({ status: 'loading' });
    setQueryResult(null);
    try {
      const response = await falkorDBApi.executeQuery(request);
      setState({ status: 'success', data: response });
      setQueryResult(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Query execution failed';
      setState({ status: 'error', error: message });
    }
  };

  const isLoading = state.status === 'loading';

  return (
    <div className="falkordb-page">
      <header className="falkordb-header">
        <div className="header-content">
          <h1>🔗 FalkorDB Graph Database</h1>
          <p>Create nodes, relationships, and query your graph database</p>
        </div>
      </header>

      <main className="falkordb-main">
        {(activeTab as ActiveTab) === 'templates' ? (
          // Full-width layout for Templates
          <div style={{ maxWidth: '1600px', margin: '0 auto' }}>
            <TemplateManager />
          </div>
        ) : (
          <div className="falkordb-layout">
            {/* Left sidebar - Data Input */}
            <aside className="falkordb-sidebar">
            <div className="tab-buttons">
              <button
                className={`tab-button ${activeTab === 'node' ? 'active' : ''}`}
                onClick={() => setActiveTab('node')}
              >
                📍 Node
              </button>
              <button
                className={`tab-button ${activeTab === 'relationship' ? 'active' : ''}`}
                onClick={() => setActiveTab('relationship')}
              >
                🔗 Relationship
              </button>
              <button
                className={`tab-button ${activeTab === 'query' ? 'active' : ''}`}
                onClick={() => setActiveTab('query')}
              >
                🔍 Query
              </button>
              <button
                className={`tab-button ${(activeTab as ActiveTab) === 'templates' ? 'active' : ''}`}
                onClick={() => setActiveTab('templates' as ActiveTab)}
              >
                📋 Templates
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'node' && (
                <NodeTemplateForm 
                  onSubmit={handleCreateNode} 
                  isLoading={isLoading}
                />
              )}
              {activeTab === 'relationship' && (
                <RelationshipForm 
                  onSubmit={handleCreateRelationship} 
                  isLoading={isLoading}
                  availableLabels={availableLabels}
                  availableRelationshipTypes={availableRelationshipTypes}
                />
              )}
              {activeTab === 'query' && (
                <QueryForm onExecute={handleExecuteQuery} isLoading={isLoading} />
              )}
            </div>
          </aside>

          {/* Center - Results */}
          <section className="falkordb-content">
            {successMessage && (
              <div className="success-banner">
                ✓ {successMessage}
              </div>
            )}

            {state.status === 'error' && (
              <div className="error-banner">
                ❌ {state.error}
              </div>
            )}

            {state.status === 'loading' && (
              <div className="loading-state">
                <div className="spinner-large"></div>
                <p>Processing request...</p>
              </div>
            )}

            {activeTab === 'query' && (
              <ResultsViewer result={queryResult} />
            )}

            {(activeTab === 'node' || activeTab === 'relationship') && state.status === 'success' && (
              <div className="success-state">
                <div className="success-icon">✓</div>
                <h3>Success!</h3>
                <pre className="success-details">
                  {JSON.stringify(state.data, null, 2)}
                </pre>
              </div>
            )}

            {state.status === 'idle' && activeTab !== 'query' && (
              <div className="idle-state">
                <div className="idle-icon">📝</div>
                <h3>Ready to Create</h3>
                <p>Fill in the form to create a {activeTab === 'node' ? 'node' : 'relationship'}</p>
              </div>
            )}
          </section>

          {/* Right sidebar - Statistics */}
          <aside className="falkordb-stats-sidebar">
            <GraphStatsCard 
              key={statsKey} 
              onStatsLoaded={(stats) => {
                setAvailableLabels(stats.labels);
                setAvailableRelationshipTypes(stats.relationship_types);
              }}
            />
          </aside>
          </div>
        )}
      </main>

      <footer className="falkordb-footer">
        <p>Powered by FalkorDB Graph Database · Cypher Query Language</p>
      </footer>
    </div>
  );
};

