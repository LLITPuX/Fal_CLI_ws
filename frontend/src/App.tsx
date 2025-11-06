import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { GeminiPage } from './pages/GeminiPage';
import { FalkorDBPage } from './pages/FalkorDBPage';
import ChatPage from './pages/ChatPage';
import './styles/App.css';

function AppContent() {
  const location = useLocation();
  const isChatPage = location.pathname === '/chat';

  return (
    <div className="app">
      {!isChatPage && <Navigation />}
      
      <Routes>
        <Route path="/" element={<GeminiPage />} />
        <Route path="/falkordb" element={<FalkorDBPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>

      {!isChatPage && (
        <footer className="app-footer">
          <p>Powered by Google Gemini AI & FalkorDB · v2.3.0</p>
        </footer>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

