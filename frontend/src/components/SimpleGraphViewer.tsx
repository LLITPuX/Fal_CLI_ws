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
  properties?: Record<string, any>;
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

// Node colors by label
const NODE_COLORS: Record<string, string> = {
  // Knowledge Base
  KnowledgeBase: '#0057B7',      // Blue
  Document: '#4CAF50',           // Green
  Chunk: '#9C27B0',              // Purple
  
  // Entities
  Entity: '#FF9800',             // Orange
  
  // User Interactions
  UserQuery: '#4CAF50',          // Green
  AssistantResponse: '#9C27B0',  // Purple
  
  // Development
  DevelopmentSession: '#FF9800', // Orange
  ArchitecturalDecision: '#F44336', // Red
  
  // Chat
  Message: '#2196F3',            // Light Blue
  ChatSession: '#00BCD4',        // Cyan
  
  // Legacy
  Person: '#0057B7',             // Blue
  Company: '#FFD700',            // Gold
  CursorSession: '#FF9800',      // Orange
  
  default: '#757575',            // Gray
};

export default function SimpleGraphViewer({ graphName, cypherQuery, autoLoad = true }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });
  const [selectedNode, setSelectedNode] = useState<VisNode | null>(null);
  const [showModal, setShowModal] = useState(false);

  /**
   * Fetch graph data from backend
   */
  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch nodes
      const nodesResponse = await fetch('/api/falkordb/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: cypherQuery || `MATCH (n) RETURN n LIMIT 500`,
          params: {},
          graph_name: graphName,
        }),
      });

      if (!nodesResponse.ok) {
        throw new Error(`Failed to fetch nodes: ${nodesResponse.statusText}`);
      }

      const nodesData = await nodesResponse.json();
      if (!nodesData.success) {
        throw new Error(nodesData.message || 'Nodes query failed');
      }

      // Fetch relationships separately for better reliability
      const edgesResponse = await fetch('/api/falkordb/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 1000`,
          params: {},
          graph_name: graphName,
        }),
      });

      let edgesData = { success: true, results: [] };
      if (edgesResponse.ok) {
        edgesData = await edgesResponse.json();
      }

      // Combine results
      // Handle case where results might be array of nodes directly or wrapped in objects
      const nodeRows = nodesData.results.map((row: any) => {
        // If row is already a node object, wrap it
        if (row.id !== undefined && row.label !== undefined) {
          return { n: row, r: null, m: null };
        }
        // If row has 'n' property, use it
        return { n: row.n || row, r: null, m: null };
      });
      
      const allResults = [
        ...nodeRows,
        ...(edgesData.results || [])
      ];

      console.log('Graph data loaded:', {
        nodeRows: nodeRows.length,
        edgeRows: edgesData.results?.length || 0,
        totalResults: allResults.length,
        sampleNode: nodeRows[0]?.n
      });

      // Transform FalkorDB results to vis-network format
      const transformedData = transformQueryResults(allResults);
      
      console.log('Transformed data:', {
        nodes: transformedData.nodes.length,
        edges: transformedData.edges.length,
        sampleNode: transformedData.nodes[0]
      });
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
   * Get smart label for node based on type and properties
   */
  const getNodeLabel = (label: string, properties: Record<string, any>): string => {
    // Document nodes
    if (label === 'Document') {
      return properties.relative_path || properties.path || `Document ${properties.id?.slice(0, 8)}`;
    }
    
    // Chunk nodes
    if (label === 'Chunk') {
      const chunkType = properties.chunk_type || 'chunk';
      const position = properties.position !== undefined ? `#${properties.position}` : '';
      return `${chunkType}${position}`;
    }
    
    // KnowledgeBase nodes
    if (label === 'KnowledgeBase') {
      return properties.id || properties.type || 'Knowledge Base';
    }
    
    // Entity nodes
    if (label === 'Entity') {
      return properties.canonical_name || properties.name || `Entity ${properties.id?.slice(0, 8)}`;
    }
    
    // UserQuery nodes
    if (label === 'UserQuery') {
      const content = properties.content || '';
      const preview = content.length > 30 ? content.substring(0, 30) + '...' : content;
      return preview || 'User Query';
    }
    
    // AssistantResponse nodes
    if (label === 'AssistantResponse') {
      const summary = properties.summary || '';
      const preview = summary.length > 30 ? summary.substring(0, 30) + '...' : summary;
      return preview || 'Response';
    }
    
    // Generic fallback
    return properties.name || properties.title || properties.id?.slice(0, 8) || label;
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
        if (node && node !== null) {
          // Handle different node formats
          let nodeId: string | number;
          let label: string;
          let properties: Record<string, any>;
          
          // Check if node is already a proper node object
          if (node.id !== undefined) {
            nodeId = node.id;
            label = node.label || node.labels?.[0] || 'Node';
            properties = node.properties || {};
          } else if (typeof node === 'object') {
            // Node might be serialized differently - try to extract ID
            nodeId = (node as any).id || (node as any).node_id || `node_${nodesMap.size}`;
            label = (node as any).label || (node as any).labels?.[0] || 'Node';
            properties = { ...node };
            // Remove id and label from properties if they exist
            delete properties.id;
            delete properties.label;
            delete properties.labels;
          } else {
            // Skip invalid nodes
            return;
          }
          
          if (!nodesMap.has(nodeId)) {
            // Get smart label
            const smartLabel = getNodeLabel(label, properties);
            
            // Create detailed title (hover info)
            const title = Object.entries(properties)
              .filter(([_k, v]) => v !== null && v !== undefined && v !== '')
              .map(([k, v]) => {
                const value = typeof v === 'string' && v.length > 100 
                  ? v.substring(0, 100) + '...' 
                  : String(v);
                return `${k}: ${value}`;
              })
              .join('\n');

            nodesMap.set(nodeId, {
              id: nodeId,
              label: smartLabel,
              group: label,
              title: title || label,
              color: NODE_COLORS[label] || NODE_COLORS.default,
              properties: properties,
            });
          }
        }
      });

      // Process relationships (r) - improved parsing
      const relationship = row.r;
      if (relationship && relationship !== null) {
        // Extract relationship type
        const relType = relationship.type || relationship.relation || 'RELATED_TO';
        
        // Extract properties
        const relProps = relationship.properties || {};
        
        // Get source and destination from row context (n -> m)
        // This is the most reliable way since FalkorDB serializes relationships
        // without explicit src/dest in the relationship object
        if (row.n && row.n.id !== undefined && row.m && row.m.id !== undefined) {
          const src = row.n.id;
          const dest = row.m.id;
          
          const edgeId = `${src}-${relType}-${dest}`;
          if (!edgesMap.has(edgeId)) {
            const title = Object.entries(relProps)
              .filter(([_k, v]) => v !== null && v !== undefined && v !== '')
              .map(([k, v]) => {
                const value = typeof v === 'string' && v.length > 100 
                  ? v.substring(0, 100) + '...' 
                  : String(v);
                return `${k}: ${value}`;
              })
              .join('\n');

            edgesMap.set(edgeId, {
              id: edgeId,
              from: src,
              to: dest,
              label: relType,
              title: title || relType,
              arrows: 'to',
            });
          }
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
              size: 0, // Hide labels by default
              color: COLORS.darkBrown,
            },
            borderWidth: 2,
            borderWidthSelected: 4,
            labelHighlightBold: false,
            chosen: {
              node: (values: any, _id: string | number, selected: boolean, hovering: boolean) => {
                // Show label on hover or selection
                if (hovering || selected) {
                  values.font = { size: 12, color: COLORS.darkBrown };
                } else {
                  values.font = { size: 0 };
                }
              },
              label: true,
            },
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
            const nodeId = params.nodes[0];
            const node = graphData.nodes.find(n => n.id === nodeId);
            if (node) {
              setSelectedNode(node);
              setShowModal(true);
            }
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
        
        {/* Node Details Modal */}
        {showModal && selectedNode && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={() => setShowModal(false)}
          >
            <div 
              className="max-w-2xl w-full mx-4 rounded-2xl border-4 shadow-2xl max-h-[80vh] overflow-y-auto"
              style={{
                backgroundColor: COLORS.beige,
                borderColor: COLORS.darkBrown,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b-2" style={{ borderColor: COLORS.darkBrown }}>
                <div className="flex items-center justify-between">
                  <h2 
                    className="text-2xl font-bold"
                    style={{ color: COLORS.darkBrown }}
                  >
                    {selectedNode.label}
                  </h2>
                  <button
                    onClick={() => setShowModal(false)}
                    className="p-2 rounded-lg hover:bg-opacity-80"
                    style={{ backgroundColor: COLORS.blue, color: 'white' }}
                  >
                    ✕
                  </button>
                </div>
                <p className="text-sm mt-2" style={{ color: COLORS.darkBrown, opacity: 0.7 }}>
                  Type: {selectedNode.group}
                </p>
              </div>
              
              <div className="p-6">
                <h3 
                  className="text-lg font-semibold mb-4"
                  style={{ color: COLORS.darkBrown }}
                >
                  Properties
                </h3>
                <div className="space-y-2">
                  {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, value]) => (
                    <div 
                      key={key}
                      className="p-3 rounded-lg border"
                      style={{ 
                        backgroundColor: 'white',
                        borderColor: COLORS.darkBrown,
                      }}
                    >
                      <div 
                        className="font-semibold text-sm mb-1"
                        style={{ color: COLORS.blue }}
                      >
                        {key}
                      </div>
                      <div 
                        className="text-sm break-words"
                        style={{ color: COLORS.darkBrown }}
                      >
                        {typeof value === 'string' && value.length > 500
                          ? value.substring(0, 500) + '...'
                          : String(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

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

