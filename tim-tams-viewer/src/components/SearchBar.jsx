import { useState, useCallback, useRef } from 'react';

function SearchBar({ tracks, events, onResults }) {
  const [query, setQuery] = useState('');
  const timerRef = useRef(null);

  const handleClear = useCallback(() => {
    setQuery('');
    onResults([], []);
  }, [onResults]);

  const handleSearch = useCallback((searchQuery) => {
    if (!searchQuery.trim()) {
      onResults([], []);
      return;
    }

    const lower = searchQuery.toLowerCase();

    const matchedSongs = [];
    if (tracks) {
      for (const track of tracks) {
        const titleMatch = track.title.toLowerCase().includes(lower);
        const artistMatch = track.artist.toLowerCase().includes(lower);
        const aliasMatch = track.aliases && track.aliases.some((a) => a.toLowerCase().includes(lower));
        if (titleMatch || artistMatch || aliasMatch) {
          matchedSongs.push(track);
        }
      }
    }

    const matchedEvents = [];
    if (events) {
      for (const event of events) {
        const titleMatch = event.title.replace(/\s+/g, '').toLowerCase().includes(lower);
        const descMatch = event.description && event.description.toLowerCase().includes(lower);
        if (titleMatch || descMatch) {
          matchedEvents.push(event);
        }
      }
    }

    onResults(matchedSongs, matchedEvents);
  }, [tracks, events, onResults]);

  const handleInput = useCallback((e) => {
    const value = e.target.value;
    setQuery(value);

    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(() => {
      handleSearch(value);
    }, 200);
  }, [handleSearch]);

  return (
    <div className="search-bar">
      <div className="search-bar-inner">
        <span className="search-bar-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        <input
          type="text"
          className="search-bar-input"
          placeholder="Search songs, artists, aliases, or events..."
          value={query}
          onChange={handleInput}
        />
        {query && (
          <button className="search-bar-clear" onClick={handleClear} aria-label="Clear search">
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

export default SearchBar;
