import { useState, useEffect, useMemo } from 'react';

function Statistics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('histograph');

  useEffect(() => {
    fetch('./data/statistics.json')
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        setError('Failed to load statistics data.');
        setLoading(false);
      });
  }, []);

  const tabs = useMemo(() => [
    { key: 'histograph', label: 'Histogram' },
    { key: 'sorted_histograph', label: 'Sorted' },
    { key: 'day_of_week', label: 'Day of Week' },
    { key: 'time_of_day', label: 'Time of Day' },
  ], []);

  const maxBinSongs = useMemo(() => {
    if (!stats) return 1;
    return Math.max(...stats.histograph.map((s) => s.bin_songs), 1);
  }, [stats]);

  const maxYoutubeFriendly = useMemo(() => {
    if (!stats) return 1;
    return Math.max(...stats.histograph.map((s) => s.youtube_friendly), 1);
  }, [stats]);

  const maxChartValue = useMemo(() => {
    return Math.max(maxBinSongs, maxYoutubeFriendly);
  }, [maxBinSongs, maxYoutubeFriendly]);

  if (loading) return <div className="loading">Loading statistics...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!stats) return null;

  return (
    <div className="statistics">
      <div className="statistics-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`statistics-tab${activeTab === tab.key ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'histograph' && (
        <div className="statistics-section">
          <div className="histogram-legend">
            <span className="histogram-legend-item">
              <span className="histogram-legend-swatch" style={{ background: 'var(--accent)' }}></span>
              Bin Songs
            </span>
            <span className="histogram-legend-item">
              <span className="histogram-legend-swatch" style={{ background: 'var(--accent-hover)' }}></span>
              YouTube Friendly
            </span>
          </div>
          <h3>Bin Songs per Stream (Chronological)</h3>
          <div className="histogram-chart">
            {stats.histograph.map((entry, i) => {
              const binHeight = (entry.bin_songs / maxChartValue) * 100;
              const youtubeHeight = (entry.youtube_friendly / maxChartValue) * 100;
              return (
                <div key={i} className="histogram-bar-wrapper">
                  <div className="histogram-bars">
                    <div
                      className="histogram-bar histogram-bar-youtube"
                      style={{ height: `${youtubeHeight}%` }}
                      title={`${entry.date} ${entry.time} — ${entry.youtube_friendly} youtube friendly`}
                    />
                    <div
                      className="histogram-bar histogram-bar-bin"
                      style={{ height: `${binHeight}%` }}
                      title={`${entry.date} ${entry.time} — ${entry.bin_songs} bin songs`}
                    />
                  </div>
                  <div className="histogram-label">{entry.bin_songs}</div>
                </div>
              );
            })}
          </div>
          <div className="histogram-dates">
            {stats.histograph.map((entry, i) => (
              <div key={i} className="histogram-date-label">
                {entry.date.split('').join('\n')}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'sorted_histograph' && (
        <div className="statistics-section">
          <div className="histogram-legend">
            <span className="histogram-legend-item">
              <span className="histogram-legend-swatch" style={{ background: 'var(--accent)' }}></span>
              Bin Songs
            </span>
            <span className="histogram-legend-item">
              <span className="histogram-legend-swatch" style={{ background: 'var(--accent-hover)' }}></span>
              YouTube Friendly
            </span>
          </div>
          <h3>Bin Songs per Stream (Sorted by Count)</h3>
          <div className="histogram-chart">
            {stats.sorted_histograph.map((entry, i) => {
              const binHeight = (entry.bin_songs / maxChartValue) * 100;
              const youtubeHeight = (entry.youtube_friendly / maxChartValue) * 100;
              return (
                <div key={i} className="histogram-bar-wrapper">
                  <div className="histogram-bars">
                    <div
                      className="histogram-bar histogram-bar-youtube"
                      style={{ height: `${youtubeHeight}%` }}
                      title={`${entry.date} ${entry.time} — ${entry.youtube_friendly} youtube friendly`}
                    />
                    <div
                      className="histogram-bar histogram-bar-bin"
                      style={{ height: `${binHeight}%` }}
                      title={`${entry.date} ${entry.time} — ${entry.bin_songs} bin songs`}
                    />
                  </div>
                  <div className="histogram-label">{entry.bin_songs}</div>
                </div>
              );
            })}
          </div>
          <div className="histogram-dates">
            {stats.sorted_histograph.map((entry, i) => (
              <div key={i} className="histogram-date-label">
                {entry.date.split('').join('\n')}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'day_of_week' && (
        <div className="statistics-section">
          <h3>Average Bin Songs by Day of Week</h3>
          <div className="stats-table">
            <table>
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Avg Bin Songs</th>
                  <th>Streams</th>
                </tr>
              </thead>
              <tbody>
                {stats.day_of_week.map((row, i) => (
                  <tr key={i}>
                    <td className="stats-day">{row.day}</td>
                    <td className="stats-value">{row.bin_songs.toFixed(2)}</td>
                    <td className="stats-count">{row.streams}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'time_of_day' && (
        <div className="statistics-section">
          <h3>Average Bin Songs by Time of Day</h3>
          <div className="stats-table">
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Avg Bin Songs</th>
                  <th>Streams</th>
                </tr>
              </thead>
              <tbody>
                {stats.time_of_day.map((row, i) => (
                  <tr key={i}>
                    <td className="stats-period">{row.period}</td>
                    <td className="stats-value">{row.bin_songs.toFixed(2)}</td>
                    <td className="stats-count">{row.streams}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Statistics;
