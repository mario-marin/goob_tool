import { useState, useEffect, useCallback, useMemo } from 'react';
import Calendar from './components/Calendar';
import StreamDetail from './components/StreamDetail';
import SearchBar from './components/SearchBar';
import TrackDialog from './components/TrackDialog';
import EventDialog from './components/EventDialog';
import { getAvailableDates, fetchStreamData } from './utils/streams';
import './App.css';

function App() {
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [streamData, setStreamData] = useState(null);
  const [tracks, setTracks] = useState(null);
  const [events, setEvents] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Search state
  const [searchResults, setSearchResults] = useState({ songs: [], events: [] });
  const [searchActive, setSearchActive] = useState(false);

  // Theme state
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  const themeIcon = useMemo(() => {
    return theme === 'dark' ? (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    ) : (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    );
  }, [theme]);

  useEffect(() => {
    getAvailableDates().then((dates) => {
      console.log('Available dates:', dates);
      setAvailableDates(dates);
      if (dates.length > 0) {
        setSelectedDate(dates[0]);
      }
    }).catch((err) => {
      console.error('Failed to load available dates:', err);
      setError('Failed to load stream data.');
    });
  }, []);

  useEffect(() => {
    fetch('./data/tracks.json')
      .then((res) => res.json())
      .then((data) => {
        setTracks(data.tracks || []);
      })
      .catch((err) => {
        console.error('Failed to load tracks data:', err);
      });
  }, []);

  useEffect(() => {
    fetch('./data/events.json')
      .then((res) => res.json())
      .then((data) => {
        setEvents(data.events || []);
      })
      .catch((err) => {
        console.error('Failed to load events data:', err);
      });
  }, []);

  const loadStreamData = useCallback(async (date) => {
    setLoading(true);
    setError(null);
    setStreamData(null);

    // Fetch the manifest to find the file for this date
    const manifestResponse = await fetch('./data/streams-manifest.json');
    const filenames = await manifestResponse.json();
    
    const matchingFiles = filenames.filter((filename) =>
      filename.includes(date)
    );

    if (matchingFiles.length === 0) {
      setError('No stream data found for this date.');
      setLoading(false);
      return;
    }

    matchingFiles.sort().reverse();
    const filePath = `./data/streams/${matchingFiles[0]}`;

    try {
      const data = await fetchStreamData(filePath);
      setStreamData(data);
    } catch (e) {
      setError('Failed to load stream data.');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectDate = useCallback(
    (date) => {
      setSelectedTrack(null);
      setSelectedEvent(null);
      setSelectedDate(date);
      loadStreamData(date);
    },
    [loadStreamData]
  );

  const handleSearchResults = useCallback((songs, events) => {
    setSearchResults({ songs, events });
    setSearchActive(songs.length > 0 || events.length > 0);
  }, []);

  const handleSearchTrackClick = useCallback((track) => {
    setSelectedTrack(track);
    setSearchActive(false);
  }, []);

  const handleSearchEventClick = useCallback((event) => {
    setSelectedEvent(event);
    setSearchActive(false);
  }, []);

  // Dialog state (lifted to App for single source of truth)
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const handleClearSearch = useCallback(() => {
    setSearchActive(false);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Tim Tams Viewer</h1>
        <p className="app-subtitle">Browse stream timestamp data</p>
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {themeIcon}
        </button>
        <a
          href="https://github.com/mario-marin/goob_tool"
          target="_blank"
          rel="noopener noreferrer"
          className="github-link"
          aria-label="View source on GitHub"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          <span className="github-link-text">Repository</span>
        </a>
      </header>

      <main className="app-main">
        <div className="calendar-panel">
          <Calendar
            availableDates={availableDates}
            selectedDate={selectedDate}
            onSelectDate={handleSelectDate}
          />
          {availableDates.length > 0 && (
            <div className="legend">
              <span className="legend-item">
                <span className="stream-dot" /> Available
              </span>
            </div>
          )}
          <SearchBar tracks={tracks || []} events={events || []} onResults={handleSearchResults} />
        </div>

        <div className="detail-panel">
          {searchActive && (
            <div className="search-results-panel">
              <div className="search-results-header">
                <h3>Search Results</h3>
                <button className="search-results-close" onClick={handleClearSearch} aria-label="Clear search">
                  ✕
                </button>
              </div>
              {searchResults.songs.length > 0 && (
                <div className="search-results-section">
                  <h4>Songs ({searchResults.songs.length})</h4>
                  <div className="search-results-list">
                    {searchResults.songs.map((track, i) => (
                      <div
                        key={i}
                        className="search-result-item search-result-song"
                        onClick={() => handleSearchTrackClick(track)}
                        style={{ cursor: 'pointer' }}
                      >
                        <span className="search-result-title">{track.title}</span>
                        {' '}
                        <span className="search-result-subtitle">{track.artist}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {searchResults.events.length > 0 && (
                <div className="search-results-section">
                  <h4>Events ({searchResults.events.length})</h4>
                  <div className="search-results-list">
                    {searchResults.events.map((event, i) => (
                      <div
                        key={i}
                        className="search-result-item search-result-event"
                        onClick={() => handleSearchEventClick(event)}
                        style={{ cursor: 'pointer' }}
                      >
                        <span className="search-result-title">{event.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {!searchActive && (
            <>
              {loading && <div className="loading">Loading...</div>}
              {error && <div className="error">{error}</div>}
              {!loading && !error && streamData && (
                <StreamDetail data={streamData} tracks={tracks} events={events} onSelectDate={handleSelectDate} onOpenTrack={setSelectedTrack} onOpenEvent={setSelectedEvent} />
              )}
              {!loading && !error && !streamData && (
                <div className="empty-state">
                  <p>Select a date to view stream data</p>
                </div>
              )}
            </>
          )}
        </div>

      </main>

      {/* Dialogs rendered at App level so they work from both search and stream detail */}
      {selectedTrack && (
        <TrackDialog track={selectedTrack} onClose={() => setSelectedTrack(null)} onSelectDate={handleSelectDate} />
      )}
      {selectedEvent && (
        <EventDialog event={selectedEvent} onClose={() => setSelectedEvent(null)} onSelectDate={handleSelectDate} />
      )}
    </div>
  );
}

export default App;
