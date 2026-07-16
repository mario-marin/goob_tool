import { useEffect, useRef } from 'react';

function TrackDialog({ track, onClose }) {
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

  if (!track) return null;

  return (
    <div
      ref={overlayRef}
      className="track-dialog-overlay"
      onClick={handleOverlayClick}
    >
      <div className="track-dialog">
        <div className="track-dialog-header">
          <h2>{track.title}</h2>
          <button className="track-dialog-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="track-dialog-body">
          {Object.entries(track)
            .filter(([key]) => key !== 'hidden')
            .map(([key, value]) => (
              <div key={key} className="track-dialog-field">
                <dt className="track-dialog-label">{key}</dt>
                <dd className="track-dialog-value">
                  {Array.isArray(value) ? (
                    value.length > 0 ? (
                      <span>{value.join(', ')}</span>
                    ) : (
                      <span className="track-dialog-empty">(empty)</span>
                    )
                  ) : typeof value === 'object' && value !== null ? (
                    <pre className="track-dialog-json">{JSON.stringify(value, null, 2)}</pre>
                  ) : (
                    <span>{value ?? <span className="track-dialog-empty">(empty)</span>}</span>
                  )}
                </dd>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

export default TrackDialog;
