import { useEffect, useRef, useMemo } from 'react';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

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

  // Build mini-calendar data from dates_played
  const miniCalendar = useMemo(() => {
    const dates = track.dates_played;
    if (!dates || dates.length === 0) return null;

    const dateSet = new Set(dates);

    // Determine the range of months to display
    const months = new Set();
    dates.forEach((d) => {
      if (d && typeof d === 'string' && d.includes('-')) {
        const [y, m] = d.split('-').map(Number);
        months.add(`${y}-${m}`);
      }
    });

    const sortedMonths = Array.from(months).sort();

    const monthGrids = sortedMonths.map((key) => {
      const [year, month] = key.split('-').map(Number);
      const daysInMonth = new Date(year, month, 0).getDate();
      const firstDayOfWeek = new Date(year, month - 1, 1).getDay();

      const cells = [];
      for (let i = 0; i < firstDayOfWeek; i++) {
        cells.push({ day: null, dateStr: null });
      }
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        cells.push({ day: d, dateStr, isPlayed: dateSet.has(dateStr) });
      }

      return { year, month, cells };
    });

    return monthGrids;
  }, [track.dates_played]);

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

          {miniCalendar && (
            <div className="track-dialog-field">
              <dt className="track-dialog-label">Played on these dates</dt>
              <dd className="track-dialog-value">
                <div className="track-dialog-calendars">
                  {miniCalendar.map((monthData, mIdx) => (
                    <div key={mIdx} className="track-dialog-mini-calendar">
                      <div className="track-dialog-mini-title">
                        {MONTH_NAMES[monthData.month - 1]} {monthData.year}
                      </div>
                      <div className="track-dialog-mini-day-headers">
                        {DAYS_OF_WEEK.map((d) => (
                          <div key={d} className="track-dialog-mini-day-label">{d}</div>
                        ))}
                      </div>
                      <div className="track-dialog-mini-body">
                        {monthData.cells.map((cell, i) => {
                          if (!cell.day) {
                            return <div key={`empty-${i}`} className="track-dialog-mini-day empty" />;
                          }
                          return (
                            <button
                              key={cell.dateStr}
                              className={`track-dialog-mini-day${cell.isPlayed ? ' has-stream' : ''}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                if (cell.isPlayed && onSelectDate) {
                                  onSelectDate(cell.dateStr);
                                }
                              }}
                              disabled={!cell.isPlayed}
                              title={cell.isPlayed ? `${cell.dateStr} - Played` : 'Not played'}
                            >
                              {cell.day}
                              {cell.isPlayed && <span className="stream-dot" />}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </dd>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TrackDialog;
