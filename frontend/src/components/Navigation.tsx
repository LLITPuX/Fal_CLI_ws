/**
 * Navigation component for switching between pages
 */

import { Link, useLocation } from 'react-router-dom';
import '../styles/Navigation.css';

export const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <span className="brand-icon">🚀</span>
          <span className="brand-text">Gemini CLI</span>
        </div>
        
        <div className="nav-links">
          <Link
            to="/"
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            <span className="link-icon">🤖</span>
            <span>Text Structurer</span>
          </Link>
          
          <Link
            to="/falkordb"
            className={`nav-link ${location.pathname === '/falkordb' ? 'active' : ''}`}
          >
            <span className="link-icon">🔗</span>
            <span>FalkorDB</span>
          </Link>
          
          <Link
            to="/chat"
            className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`}
          >
            <span className="link-icon">💬</span>
            <span>Cybersich Chat</span>
          </Link>
        </div>
      </div>
    </nav>
  );
};

