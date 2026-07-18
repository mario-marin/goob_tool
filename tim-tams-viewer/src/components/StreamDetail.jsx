import { useState, useCallback, useMemo } from 'react';

function StreamDetail({ data, tracks, events, onSelectDate, onOpenTrack, onOpenEvent }) {
  const [hideFiller, setHideFiller] = useState(false);

  const isFiller = (song) =>
    song.artist === 'Esther Abrami' &&
    song.song_title === "No.9 Frank's Waltz";

  const filteredSongs = useMemo(() => {
    if (!data.songs) return [];
    if (!hideFiller) return data.songs;
    return data.songs.filter((song) => !isFiller(song));
  }, [data.songs, hideFiller]);

  const fillerCount = useMemo(() => {
    if (!data.songs) return 0;
    return data.songs.filter(isFiller).length;
  }, [data.songs]);

  const handleSongClick = useCallback((song) => {
    if (!tracks) return;
    const found = tracks.find(
      (t) =>
        t.title.toLowerCase() === song.song_title.toLowerCase() &&
        t.artist.toLowerCase() === song.artist.toLowerCase()
    );
    if (found) {
      onOpenTrack(found);
    }
  }, [tracks]);

  const handleEventClick = useCallback((event) => {
    if (!events) return;
    const found = events.find(
      (e) =>
        e.title.toLowerCase() === event.name.toLowerCase()
    );
    if (found) {
      onOpenEvent(found);
    }
  }, [events]);

  if (!data) return null;

  return (
    <div className="stream-detail">
      <div className="stream-header">
        <h2>
          {data.date} at {data.time}
        </h2>
        {data.floatplane_link && (
          <a
            href={data.floatplane_link}
            target="_blank"
            rel="noopener noreferrer"
            className="stream-detail-link"
          >
            Floatplane Stream Link ↗
          </a>
        )}
      </div>

      {data.songs && data.songs.length > 0 && (
        <div className="stream-section">
          <div className="songs-section-header">
            <h3>Songs ({filteredSongs.length}{fillerCount > 0 && hideFiller ? ` / ${data.songs.length}` : ''})</h3>
            {fillerCount > 0 && (
              <label className="filler-toggle">
                <input
                  type="checkbox"
                  checked={hideFiller}
                  onChange={(e) => setHideFiller(e.target.checked)}
                />
                <span className="filler-toggle-label">Hide Frank's Waltz</span>
              </label>
            )}
          </div>
          <div className="songs-list">
            {filteredSongs.map((song, i) => (
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

    </div>
  );
}

export default StreamDetail;
