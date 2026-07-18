import { useEffect, useRef } from 'react';

function TrackDialog({ track, onClose, onSelectDate }) {
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

  const dateFields = [
    { key: 'last_time_played', label: 'Last played' },
    { key: 'date_with_most_reproductions', label: 'Most reproductions' },
  ];

  const hasNavigableDates = dateFields.some((f) => track[f.key]);

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
            .map(([key, value]) => {
              const dateInfo = dateFields.find((f) => f.key === key);
              const isDate = dateInfo && typeof value === 'string' && value.includes('-');

              const isYouTubeLink = typeof value === 'string' && (value.startsWith('https://www.youtube.com/') || value.startsWith('https://youtu.be/'));

              return (
                <div key={key} className="track-dialog-field">
                  <dt className="track-dialog-label">{dateInfo?.label || key}</dt>
                  <dd className="track-dialog-value">
                    {Array.isArray(value) ? (
                      value.length > 0 ? (
                        <span>{value.join(', ')}</span>
                      ) : (
                        <span className="track-dialog-empty">(empty)</span>
                      )
                    ) : typeof value === 'object' && value !== null ? (
                      <pre className="track-dialog-json">{JSON.stringify(value, null, 2)}</pre>
                    ) : isDate ? (
                      <button
                        className="track-dialog-date"
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectDate && onSelectDate(value);
                        }}
                        title={onSelectDate ? 'Click to view this date' : undefined}
                      >
                        {value}
                      </button>
                    ) : isYouTubeLink ? (
                      <a
                        className="track-dialog-youtube"
                        href={value}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {value}
                      </a>
                    ) : (
                      <span>{value ?? <span className="track-dialog-empty">(empty)</span>}</span>
                    )}
                  </dd>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}

export default TrackDialog;
