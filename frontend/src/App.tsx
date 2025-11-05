import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { GeminiPage } from './pages/GeminiPage';
import { FalkorDBPage } from './pages/FalkorDBPage';
import ChatPage from './pages/ChatPage';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        
        <Routes>
          <Route path="/" element={<GeminiPage />} />
          <Route path="/falkordb" element={<FalkorDBPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>

        <footer className="app-footer">
          <p>Powered by Google Gemini AI & FalkorDB · v2.3.0</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

