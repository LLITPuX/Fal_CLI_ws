/**
 * Simple Graph Viewer Component - Custom FalkorDB Visualization
 * Використовує vis-network для простої та ефективної візуалізації графа
 */

import { useEffect, useRef, useState } from 'react';
import { RefreshCw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

// Types для vis-network (будуть імпортовані після встановлення пакету)
interface VisNode {
  id: number | string;
  label: string;
  group?: string;
  title?: string;
  color?: string;
}

interface VisEdge {
  id: string;
  from: number | string;
  to: number | string;
  label?: string;
  title?: string;
  arrows?: string;
}

interface GraphData {
  nodes: VisNode[];
  edges: VisEdge[];
}

interface Props {
  graphName: string;
  cypherQuery?: string;
  autoLoad?: boolean;
}

// Cossack color palette
const COLORS = {
  beige: '#F3EDDC',
  darkBrown: '#2F2F27',
  gold: '#FFD700',
  blue: '#0057B7',
  yellow: '#FFD700',
};

// Node colors by label (можна розширювати)
const NODE_COLORS: Record<string, string> = {
  Person: '#0057B7',      // Blue
  Company: '#FFD700',     // Gold
  UserQuery: '#4CAF50',   // Green
  AIResponse: '#9C27B0',  // Purple
  CursorSession: '#FF9800', // Orange
  ArchitecturalDecision: '#F44336', // Red
  default: '#757575',     // Gray
};

export default function SimpleGraphViewer({ graphName, cypherQuery, autoLoad = true }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });

  // Default query - отримати всі вузли та зв'язки (з лімітом)
  const defaultQuery = cypherQuery || `
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n, r, m
    LIMIT 50
  `;

  /**
   * Fetch graph data from backend
   */
  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/falkordb/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: defaultQuery,
          params: {},
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch graph data: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Query failed');
      }

      // Transform FalkorDB results to vis-network format
      const transformedData = transformQueryResults(data.results);
      setGraphData(transformedData);
      setStats({
        nodes: transformedData.nodes.length,
        edges: transformedData.edges.length,
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Graph fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Transform FalkorDB query results to vis-network format
   */
  const transformQueryResults = (results: any[]): GraphData => {
    const nodesMap = new Map<string | number, VisNode>();
    const edgesMap = new Map<string, VisEdge>();

    results.forEach((row) => {
      // Process nodes (n, m)
      ['n', 'm'].forEach((key) => {
        const node = row[key];
        if (node && node.id !== undefined) {
          const nodeId = node.id;
          if (!nodesMap.has(nodeId)) {
            const label = node.label || 'Node';
            const properties = node.properties || {};
            
            // Create node title (hover info)
            const title = Object.entries(properties)
              .map(([k, v]) => `${k}: ${v}`)
              .join('\n');

            nodesMap.set(nodeId, {
              id: nodeId,
              label: properties.name || properties.title || `${label} ${nodeId}`,
              group: label,
              title: title || label,
              color: NODE_COLORS[label] || NODE_COLORS.default,
            });
          }
        }
      });

      // Process relationships (r)
      const relationship = row.r;
      if (relationship && relationship.src !== undefined && relationship.dest !== undefined) {
        const edgeId = `${relationship.src}-${relationship.type}-${relationship.dest}`;
        if (!edgesMap.has(edgeId)) {
          const relProps = relationship.properties || {};
          const title = Object.entries(relProps)
            .map(([k, v]) => `${k}: ${v}`)
            .join('\n');

          edgesMap.set(edgeId, {
            id: edgeId,
            from: relationship.src,
            to: relationship.dest,
            label: relationship.type,
            title: title || relationship.type,
            arrows: 'to',
          });
        }
      }
    });

    return {
      nodes: Array.from(nodesMap.values()),
      edges: Array.from(edgesMap.values()),
    };
  };

  /**
   * Initialize vis-network
   */
  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    // Динамічний імпорт vis-network (буде працювати після npm install)
    import('vis-network/standalone')
      .then(({ Network, DataSet }) => {
        const nodes = new DataSet(graphData.nodes);
        const edges = new DataSet(graphData.edges);

        const data = { nodes, edges };

        const options = {
          nodes: {
            shape: 'dot',
            size: 20,
            font: {
              size: 14,
              color: COLORS.darkBrown,
              bold: {
                color: COLORS.darkBrown,
              },
            },
            borderWidth: 2,
            borderWidthSelected: 4,
          },
          edges: {
            width: 2,
            color: {
              color: COLORS.darkBrown,
              highlight: COLORS.blue,
              hover: COLORS.gold,
            },
            font: {
              size: 12,
              color: COLORS.darkBrown,
              align: 'middle',
            },
            arrows: {
              to: {
                enabled: true,
                scaleFactor: 0.5,
              },
            },
            smooth: {
              enabled: true,
              type: 'continuous',
              roundness: 0.5,
            },
          },
          physics: {
            enabled: true,
            stabilization: {
              iterations: 100,
            },
            barnesHut: {
              gravitationalConstant: -2000,
              springConstant: 0.04,
              springLength: 95,
            },
          },
          interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true,
          },
        };

        // Destroy previous network if exists
        if (networkRef.current) {
          networkRef.current.destroy();
        }

        // Create new network
        networkRef.current = new Network(containerRef.current!, data, options);

        // Add event listeners
        networkRef.current.on('click', (params: any) => {
          if (params.nodes.length > 0) {
            console.log('Node clicked:', params.nodes[0]);
          }
          if (params.edges.length > 0) {
            console.log('Edge clicked:', params.edges[0]);
          }
        });
      })
      .catch((err) => {
        console.error('Failed to load vis-network:', err);
        setError('Failed to initialize graph visualization. Make sure vis-network is installed.');
      });

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData]);

  /**
   * Auto-load graph data on mount
   */
  useEffect(() => {
    if (autoLoad) {
      fetchGraphData();
    }
  }, [graphName, autoLoad]);

  /**
   * Control functions
   */
  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: true });
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Control Bar */}
      <div 
        className="flex items-center justify-between p-4 border-b-2"
        style={{ 
          backgroundColor: COLORS.beige,
          borderColor: COLORS.darkBrown,
        }}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold" style={{ color: COLORS.darkBrown }}>
            📊 {stats.nodes} вузлів · 🔗 {stats.edges} зв'язків
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-lg hover:bg-opacity-80 transition-colors"
            style={{ backgroundColor: COLORS.gold, color: COLORS.blue }}
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-lg hover:bg-opacity-80 transition-colors"
            style={{ backgroundColor: COLORS.gold, color: COLORS.blue }}
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleFit}
            className="p-2 rounded-lg hover:bg-opacity-80 transition-colors"
            style={{ backgroundColor: COLORS.gold, color: COLORS.blue }}
            title="Fit to Screen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={fetchGraphData}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
            style={{ backgroundColor: COLORS.blue, color: 'white' }}
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
            <div className="text-center">
              <div 
                className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
                style={{ borderColor: COLORS.blue, borderTopColor: 'transparent' }}
              />
              <p className="text-lg font-semibold" style={{ color: COLORS.darkBrown }}>
                Завантаження графа...
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
            <div className="max-w-md p-6 rounded-xl border-2" style={{ borderColor: '#ef4444' }}>
              <h3 className="text-xl font-bold mb-2" style={{ color: '#ef4444' }}>
                Помилка завантаження
              </h3>
              <p className="text-sm mb-4" style={{ color: COLORS.darkBrown }}>
                {error}
              </p>
              <button
                onClick={fetchGraphData}
                className="px-4 py-2 rounded-lg font-semibold"
                style={{ backgroundColor: COLORS.blue, color: 'white' }}
              >
                Спробувати знову
              </button>
            </div>
          </div>
        )}

        <div 
          ref={containerRef} 
          className="w-full h-full"
          style={{ backgroundColor: 'white' }}
        />

        {!loading && !error && graphData && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-lg font-semibold" style={{ color: COLORS.darkBrown }}>
                Граф порожній або немає результатів
              </p>
              <p className="text-sm mt-2" style={{ color: COLORS.darkBrown, opacity: 0.7 }}>
                Спробуйте інший граф або додайте дані
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

