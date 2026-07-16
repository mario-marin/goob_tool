import { useState, useCallback } from 'react';
import TrackDialog from './TrackDialog';
import EventDialog from './EventDialog';

function StreamDetail({ data, tracks, events }) {
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const handleSongClick = useCallback((song) => {
    if (!tracks) return;
    const found = tracks.find(
      (t) =>
        t.title.toLowerCase() === song.song_title.toLowerCase() &&
        t.artist.toLowerCase() === song.artist.toLowerCase()
    );
    if (found) {
      setSelectedTrack(found);
    }
  }, [tracks]);

  const handleEventClick = useCallback((event) => {
    if (!events) return;
    const found = events.find(
      (e) =>
        e.title.toLowerCase() === event.name.toLowerCase()
    );
    if (found) {
      setSelectedEvent(found);
    }
  }, [events]);

  const handleCloseTrackDialog = useCallback(() => {
    setSelectedTrack(null);
  }, []);

  const handleCloseEventDialog = useCallback(() => {
    setSelectedEvent(null);
  }, []);

  if (!data) return null;

  return (
    <div className="stream-detail">
      <div className="stream-header">
        <h2>
          {data.date} at {data.time}
        </h2>
      </div>

      {data.songs && data.songs.length > 0 && (
        <div className="stream-section">
          <h3>Songs ({data.songs.length})</h3>
          <div className="songs-list">
            {data.songs.map((song, i) => (
              <div
                key={i}
                className="song-row"
                onClick={() => handleSongClick(song)}
                style={{ cursor: 'pointer' }}
              >
                <span className="song-time">{song.time}</span>
                <span className="song-artist">{song.artist}</span>
                <span className="song-title">{song.song_title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.events && data.events.length > 0 && (
        <div className="stream-section">
          <h3>Events ({data.events.length})</h3>
          <div className="events-list">
            {data.events.map((event, i) => (
              <div
                key={i}
                className="event-row"
                onClick={() => handleEventClick(event)}
                style={{ cursor: 'pointer' }}
              >
                <span className="event-time">{event.time}</span>
                <span className="event-name">{event.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedTrack && (
        <TrackDialog track={selectedTrack} onClose={handleCloseTrackDialog} />
      )}

      {selectedEvent && (
        <EventDialog event={selectedEvent} onClose={handleCloseEventDialog} />
      )}
    </div>
  );
}

export default StreamDetail;
