function StreamDetail({ data }) {
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
              <div key={i} className="song-row">
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
              <div key={i} className="event-row">
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
