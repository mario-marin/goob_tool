import { useEffect, useRef } from 'react';

function EventDialog({ event, onClose }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) {
      onClose();
    }
  };

  if (!event) return null;

  return (
    <div
      ref={overlayRef}
      className="event-dialog-overlay"
      onClick={handleOverlayClick}
    >
      <div className="event-dialog">
        <div className="event-dialog-header">
          <h2>{event.title}</h2>
          <button className="event-dialog-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="event-dialog-body">
          {Object.entries(event)
            .filter(([key]) => key !== 'hidden')
            .map(([key, value]) => (
              <div key={key} className="event-dialog-field">
                <dt className="event-dialog-label">{key}</dt>
                <dd className="event-dialog-value">
                  {Array.isArray(value) ? (
                    value.length > 0 ? (
                      <span>{value.join(', ')}</span>
                    ) : (
                      <span className="event-dialog-empty">(empty)</span>
                    )
                  ) : typeof value === 'object' && value !== null ? (
                    <pre className="event-dialog-json">{JSON.stringify(value, null, 2)}</pre>
                  ) : (
                    <span>{value ?? <span className="event-dialog-empty">(empty)</span>}</span>
                  )}
                </dd>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

export default EventDialog;
