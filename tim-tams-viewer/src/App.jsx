import { useState, useEffect, useCallback } from 'react';
import Calendar from './components/Calendar';
import StreamDetail from './components/StreamDetail';
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
      setSelectedDate(date);
      loadStreamData(date);
    },
    [loadStreamData]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>Tim Tams Viewer</h1>
        <p className="app-subtitle">Browse stream timestamp data</p>
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
        </div>

        <div className="detail-panel">
          {loading && <div className="loading">Loading...</div>}
          {error && <div className="error">{error}</div>}
          {!loading && !error && streamData && (
            <StreamDetail data={streamData} tracks={tracks} events={events} />
          )}
          {!loading && !error && !streamData && (
            <div className="empty-state">
              <p>Select a date to view stream data</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
