/**
 * Graph Visualization Page - FalkorDB Browser Integration
 * Same Cossack design as ChatPage
 */

import { useState, useEffect } from 'react';
import { Network, Database, Sparkles, Activity, RefreshCw } from 'lucide-react';
import { CybersichHeader } from '../components/CybersichHeader';
import { falkorDBApi } from '../services/falkordb-api';

// Same background image as ChatPage - Cossack warriors!
const backgroundImage = '/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png';

// Cossack color palette
const COLORS = {
  beige: '#F3EDDC',
  darkBrown: '#2F2F27',
  gold: '#FFD700',
  blue: '#0057B7',
};

type ActiveView = 'browser' | 'stats';

interface GraphStats {
  node_count: number;
  edge_count: number;
  labels: string[];
  relationship_types: string[];
  graph_name: string;
}

// Доступні графи
const AVAILABLE_GRAPHS = [
  { value: 'gemini_graph', label: 'Gemini Graph (default)' },
  { value: 'cybersich_chat', label: 'Cybersich Chat' },
  { value: 'cursor_memory', label: 'Cursor Memory' },
];

export default function GraphVisualizationPage() {
  const [activeView, setActiveView] = useState<ActiveView>('browser');
  const [selectedGraph, setSelectedGraph] = useState<string>('gemini_graph');

  // FalkorDB Browser URL з автоматичним підключенням
  const getBrowserUrl = () => {
    const params = new URLSearchParams({
      host: 'localhost',
      port: '6379',
      graph: selectedGraph,
    });
    return `http://localhost:3001/?${params.toString()}`;
  };

  return (
    <div 
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(243, 237, 220, 0.75), rgba(243, 237, 220, 0.75)), url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Universal Cybersich Header */}
      <CybersichHeader 
        title="Cybersich" 
        subtitle="AI Помічник · Граф Знань Січі" 
      />
      
      <div className="max-w-7xl mx-auto h-[calc(100vh-80px)] flex flex-col gap-6 pt-6">

        {/* Graph Selector */}
        <div className="px-6">
          <div 
            className="rounded-2xl p-4 border-4 shadow-2xl"
            style={{
              backgroundColor: COLORS.beige,
              borderColor: COLORS.darkBrown,
            }}
          >
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5" style={{ color: COLORS.blue }} />
              <span 
                className="text-sm font-semibold"
                style={{ color: COLORS.darkBrown }}
              >
                Граф:
              </span>
              <select
                value={selectedGraph}
                onChange={(e) => setSelectedGraph(e.target.value)}
                className="flex-1 px-4 py-2 rounded-lg border-2 font-medium text-sm"
                style={{
                  backgroundColor: 'white',
                  borderColor: COLORS.darkBrown,
                  color: COLORS.darkBrown,
                }}
              >
                {AVAILABLE_GRAPHS.map((graph) => (
                  <option key={graph.value} value={graph.value}>
                    {graph.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tabs Section */}
        <div className="px-6">
          <div 
            className="rounded-2xl p-4 border-4 shadow-2xl"
            style={{
              backgroundColor: COLORS.beige,
              borderColor: COLORS.darkBrown,
            }}
          >
            <div className="flex gap-3">
              <TabButton
                icon={<Network className="w-5 h-5" />}
                label="Візуалізація Графа"
                active={activeView === 'browser'}
                onClick={() => setActiveView('browser')}
              />
              <TabButton
                icon={<Database className="w-5 h-5" />}
                label="Статистика"
                active={activeView === 'stats'}
                onClick={() => setActiveView('stats')}
              />
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden min-h-0 px-6">
          <div 
            className="rounded-2xl overflow-hidden border-4 h-full shadow-2xl"
            style={{
              backgroundColor: COLORS.beige,
              borderColor: COLORS.darkBrown,
            }}
          >
            {activeView === 'browser' ? (
              <div className="h-full overflow-y-auto p-12">
                <div className="max-w-2xl mx-auto space-y-6">
                  {/* Header */}
                  <div className="text-center">
                    <div 
                      className="w-24 h-24 rounded-full flex items-center justify-center mb-6 border-4 mx-auto"
                      style={{ 
                        backgroundColor: COLORS.gold,
                        borderColor: COLORS.blue,
                      }}
                    >
                      <Network className="w-12 h-12" style={{ color: COLORS.blue }} />
                    </div>
                    
                    <h3 
                      className="text-2xl font-bold mb-4"
                      style={{ color: COLORS.darkBrown }}
                    >
                      FalkorDB Browser
                    </h3>
                    
                    <p 
                      className="text-base mb-6"
                      style={{ color: COLORS.darkBrown, opacity: 0.7 }}
                    >
                      Візуалізація вузлів і зв'язків графа
                    </p>
                  </div>

                  {/* Instructions */}
                  <div 
                    className="rounded-xl p-6 border-2"
                    style={{
                      backgroundColor: 'white',
                      borderColor: COLORS.blue,
                    }}
                  >
                    <h4 
                      className="text-lg font-bold mb-4 flex items-center gap-2"
                      style={{ color: COLORS.blue }}
                    >
                      <Sparkles className="w-5 h-5" />
                      Інструкція підключення
                    </h4>
                    
                    <ol className="space-y-3 text-sm" style={{ color: COLORS.darkBrown }}>
                      <li className="flex gap-2">
                        <span className="font-bold">1.</span>
                        <span>Натисніть кнопку "Відкрити Browser" нижче</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="font-bold">2.</span>
                        <span>На сторінці логіну залиште всі поля як є (host: localhost, port: 6379)</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="font-bold">3.</span>
                        <span><strong>Очистіть поля Username і Password</strong> (залиште їх порожніми)</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="font-bold">4.</span>
                        <span>Натисніть "Log in"</span>
                      </li>
                      <li className="flex gap-2">
                        <span className="font-bold">5.</span>
                        <span>Виберіть граф: <strong style={{ color: COLORS.blue }}>{selectedGraph}</strong></span>
                      </li>
                    </ol>
                  </div>

                  {/* Open Button */}
                  <div className="text-center">
                    <button
                      onClick={() => window.open('http://localhost:3001', '_blank', 'noopener,noreferrer')}
                      className="px-8 py-4 rounded-xl font-bold text-lg border-3 transition-all hover:scale-105"
                      style={{
                        backgroundColor: COLORS.blue,
                        color: 'white',
                        border: `3px solid ${COLORS.gold}`,
                      }}
                    >
                      🔍 Відкрити Browser
                    </button>
                  </div>

                  {/* Technical Info */}
                  <div 
                    className="rounded-xl p-4 border"
                    style={{
                      backgroundColor: COLORS.gold,
                      borderColor: COLORS.blue,
                      opacity: 0.9,
                    }}
                  >
                    <p className="text-xs text-center" style={{ color: COLORS.blue }}>
                      📍 Connection: localhost:6379 | 👤 User: default (no password) | 📊 Graph: {selectedGraph}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <GraphStats graphName={selectedGraph} />
            )}
          </div>
        </main>

        {/* Footer - Cossack Wisdom */}
        <footer className="px-6 pb-6">
          <div 
            className="rounded-2xl p-4 text-center border-2"
            style={{
              backgroundColor: COLORS.darkBrown,
              borderColor: COLORS.gold,
              color: COLORS.beige,
            }}
          >
            <p className="flex items-center justify-center gap-2 text-sm">
              <Sparkles className="w-4 h-4" style={{ color: COLORS.gold }} />
              <span>Powered by FalkorDB · Cypher Query Language · Cybersich AI</span>
              <Sparkles className="w-4 h-4" style={{ color: COLORS.gold }} />
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

// Tab Button Component
interface TabButtonProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

function TabButton({ icon, label, active, onClick }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className="px-6 py-3 rounded-lg border-2 font-semibold transition-all flex items-center gap-2"
      style={{
        backgroundColor: active ? COLORS.gold : 'transparent',
        borderColor: active ? COLORS.blue : COLORS.darkBrown,
        color: active ? COLORS.blue : COLORS.darkBrown,
        transform: active ? 'scale(1.05)' : 'scale(1)',
        boxShadow: active ? `0 4px 12px rgba(0, 87, 183, 0.3)` : 'none',
      }}
    >
      {icon}
      {label}
    </button>
  );
}

// Graph Stats Component
interface GraphStatsProps {
  graphName: string;
}

function GraphStats({ graphName }: GraphStatsProps) {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await falkorDBApi.getStats(graphName);
      setStats(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load stats';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [graphName]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div 
            className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: COLORS.blue, borderTopColor: 'transparent' }}
          />
          <p 
            className="text-lg font-semibold"
            style={{ color: COLORS.darkBrown }}
          >
            Завантаження статистики...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div 
          className="rounded-xl p-6 border-2 max-w-md"
          style={{
            backgroundColor: 'white',
            borderColor: '#ef4444',
          }}
        >
          <div className="text-center mb-4">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 border-2"
              style={{ 
                backgroundColor: '#fef2f2',
                borderColor: '#ef4444',
              }}
            >
              <Activity className="w-8 h-8" style={{ color: '#ef4444' }} />
            </div>
            <h3 className="text-xl font-bold mb-2" style={{ color: '#ef4444' }}>
              Помилка завантаження
            </h3>
            <p className="text-sm" style={{ color: COLORS.darkBrown }}>
              {error}
            </p>
          </div>
          <button
            onClick={loadStats}
            className="w-full px-4 py-2 rounded-lg font-semibold flex items-center justify-center gap-2"
            style={{
              backgroundColor: COLORS.blue,
              color: 'white',
            }}
          >
            <RefreshCw className="w-4 h-4" />
            Спробувати знову
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Network className="w-8 h-8" />}
          label="Вузли (Nodes)"
          value={stats.node_count}
          color="blue"
        />
        <StatCard
          icon={<Database className="w-8 h-8" />}
          label="Зв'язки (Edges)"
          value={stats.edge_count}
          color="gold"
        />
        <StatCard
          icon={<Sparkles className="w-8 h-8" />}
          label="Типи Вузлів"
          value={stats.labels?.length || 0}
          color="blue"
        />
        <StatCard
          icon={<Activity className="w-8 h-8" />}
          label="Типи Зв'язків"
          value={stats.relationship_types?.length || 0}
          color="gold"
        />
      </div>

      {/* Graph Name */}
      <div 
        className="rounded-xl p-6 mb-6 border-2"
        style={{
          backgroundColor: 'white',
          borderColor: COLORS.darkBrown,
        }}
      >
        <h3 
          className="text-2xl font-bold flex items-center gap-2"
          style={{ color: COLORS.darkBrown }}
        >
          <Database className="w-6 h-6" style={{ color: COLORS.blue }} />
          Graph: <span style={{ color: COLORS.blue }}>{stats.graph_name}</span>
        </h3>
      </div>

      {/* Node Labels */}
      {stats.labels && stats.labels.length > 0 && (
        <div 
          className="rounded-xl p-6 mb-6 border-2"
          style={{
            backgroundColor: 'white',
            borderColor: COLORS.darkBrown,
          }}
        >
          <h3 
            className="text-2xl font-bold mb-4 flex items-center gap-2"
            style={{ color: COLORS.darkBrown }}
          >
            <Network className="w-6 h-6" style={{ color: COLORS.blue }} />
            Типи Вузлів
          </h3>
          <div className="flex flex-wrap gap-2">
            {stats.labels.map((label: string) => (
              <span
                key={label}
                className="px-4 py-2 rounded-full font-semibold text-sm"
                style={{
                  backgroundColor: COLORS.gold,
                  color: COLORS.blue,
                  border: `2px solid ${COLORS.blue}`,
                }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Relationship Types */}
      {stats.relationship_types && stats.relationship_types.length > 0 && (
        <div 
          className="rounded-xl p-6 border-2"
          style={{
            backgroundColor: 'white',
            borderColor: COLORS.darkBrown,
          }}
        >
          <h3 
            className="text-2xl font-bold mb-4 flex items-center gap-2"
            style={{ color: COLORS.darkBrown }}
          >
            <Activity className="w-6 h-6" style={{ color: COLORS.blue }} />
            Типи Зв'язків
          </h3>
          <div className="flex flex-wrap gap-2">
            {stats.relationship_types.map((type: string) => (
              <span
                key={type}
                className="px-4 py-2 rounded-full font-semibold text-sm"
                style={{
                  backgroundColor: COLORS.blue,
                  color: 'white',
                  border: `2px solid ${COLORS.gold}`,
                }}
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {stats.node_count === 0 && (
        <div 
          className="rounded-xl p-12 border-2 text-center"
          style={{
            backgroundColor: 'white',
            borderColor: COLORS.darkBrown,
          }}
        >
          <div 
            className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 border-4"
            style={{ 
              backgroundColor: COLORS.gold,
              borderColor: COLORS.blue,
            }}
          >
            <Database className="w-10 h-10" style={{ color: COLORS.blue }} />
          </div>
          <h3 
            className="text-2xl font-bold mb-2"
            style={{ color: COLORS.darkBrown }}
          >
            Граф порожній
          </h3>
          <p 
            className="text-sm"
            style={{ color: COLORS.darkBrown, opacity: 0.7 }}
          >
            Почніть використовувати чат або створіть вузли через API
          </p>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'blue' | 'gold';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const iconBgColor = color === 'gold' ? COLORS.gold : COLORS.blue;
  const iconBorderColor = color === 'gold' ? COLORS.blue : COLORS.gold;
  const iconColor = color === 'gold' ? COLORS.blue : 'white';

  return (
    <div 
      className="rounded-xl p-6 border-2 transition-transform hover:scale-105"
      style={{
        backgroundColor: 'white',
        borderColor: COLORS.darkBrown,
        boxShadow: `0 4px 12px rgba(47, 47, 39, 0.15)`,
      }}
    >
      <div 
        className="w-12 h-12 rounded-full flex items-center justify-center mb-4 border-2"
        style={{ 
          backgroundColor: iconBgColor,
          borderColor: iconBorderColor,
        }}
      >
        <div style={{ color: iconColor }}>{icon}</div>
      </div>
      <div 
        className="text-3xl font-bold mb-2"
        style={{ color: COLORS.darkBrown }}
      >
        {value.toLocaleString()}
      </div>
      <div 
        className="text-sm font-medium"
        style={{ color: COLORS.darkBrown, opacity: 0.7 }}
      >
        {label}
      </div>
    </div>
  );
}

