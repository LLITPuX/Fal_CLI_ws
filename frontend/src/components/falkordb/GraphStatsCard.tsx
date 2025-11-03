/**
 * Displays graph database statistics
 */

import { useEffect, useState } from 'react';
import { falkorDBApi } from '../../services/falkordb-api';
import type { GraphStats } from '../../types/falkordb';

interface GraphStatsCardProps {
  onStatsLoaded?: (stats: GraphStats) => void;
}

export const GraphStatsCard = ({ onStatsLoaded }: GraphStatsCardProps) => {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await falkorDBApi.getStats();
      setStats(data);
      onStatsLoaded?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (loading && !stats) {
    return (
      <div className="stats-card loading">
        <div className="spinner-small"></div>
        <p>Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stats-card error">
        <p>❌ {error}</p>
        <button onClick={loadStats} className="btn-secondary">
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="stats-card">
      <div className="stats-header">
        <h3>📈 Graph Statistics</h3>
        <button onClick={loadStats} className="btn-icon" title="Refresh">
          🔄
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">{stats.node_count}</div>
          <div className="stat-label">Nodes</div>
        </div>

        <div className="stat-item">
          <div className="stat-value">{stats.edge_count}</div>
          <div className="stat-label">Relationships</div>
        </div>

        <div className="stat-item">
          <div className="stat-value">{stats.labels.length}</div>
          <div className="stat-label">Labels</div>
        </div>

        <div className="stat-item">
          <div className="stat-value">{stats.relationship_types.length}</div>
          <div className="stat-label">Relation Types</div>
        </div>
      </div>

      {stats.labels.length > 0 && (
        <div className="stats-detail">
          <h4>Labels:</h4>
          <div className="tags">
            {stats.labels.map((label) => (
              <span key={label} className="tag">
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {stats.relationship_types.length > 0 && (
        <div className="stats-detail">
          <h4>Relationship Types:</h4>
          <div className="tags">
            {stats.relationship_types.map((type) => (
              <span key={type} className="tag">
                {type}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="stats-footer">
        <small>Graph: {stats.graph_name}</small>
      </div>
    </div>
  );
};

