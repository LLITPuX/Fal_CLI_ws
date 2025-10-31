interface ErrorMessageProps {
  message: string;
  onDismiss: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  return (
    <div className="error-message">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <div className="error-text">
          <h4>Error</h4>
          <p>{message}</p>
        </div>
        <button onClick={onDismiss} className="dismiss-btn" aria-label="Dismiss error">
          ✕
        </button>
      </div>
    </div>
  );
};

