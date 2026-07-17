import { useState, useMemo, useEffect } from 'react';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function Calendar({ availableDates, selectedDate, onSelectDate }) {
  const [currentDate, setCurrentDate] = useState(() => {
    // Start at the latest available month
    if (availableDates.length > 0) {
      const latest = availableDates[0]; // YYYY-MM-DD
      const [y, m] = latest.split('-').map(Number);
      return new Date(y, m - 1, 1);
    }
    return new Date();
  });

  // Sync displayed month to selected date
  useEffect(() => {
    if (selectedDate) {
      const [y, m] = selectedDate.split('-').map(Number);
      setCurrentDate(new Date(y, m - 1, 1));
    }
  }, [selectedDate]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();

  const prevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  // Build the grid of days
  const calendarDays = useMemo(() => {
    const days = [];
    // Empty cells before the 1st
    for (let i = 0; i < firstDayOfWeek; i++) {
      days.push({ day: null, dateStr: null });
    }
    // Actual days
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      days.push({ day: d, dateStr, hasStream: availableDates.includes(dateStr) });
    }
    return days;
  }, [year, month, daysInMonth, firstDayOfWeek, availableDates]);

  const isCurrentMonth = (dateStr) => {
    if (!dateStr) return false;
    const [y, m] = dateStr.split('-').map(Number);
    return y === year && m === month + 1;
  };

  const isSelected = (dateStr) => dateStr === selectedDate;

  return (
    <div className="calendar">
      <div className="calendar-header">
        <button className="calendar-nav" onClick={prevMonth}>&#9664;</button>
        <h2 className="calendar-title">
          {MONTH_NAMES[month]} {year}
        </h2>
        <button className="calendar-nav" onClick={nextMonth}>&#9654;</button>
      </div>
      <div className="calendar-grid">
        <div className="calendar-day-header">
          {DAYS_OF_WEEK.map((d) => (
            <div key={d} className="calendar-day-label">{d}</div>
          ))}
        </div>
        <div className="calendar-body">
          {calendarDays.map((cell, i) => {
            if (!cell.day) {
              return <div key={`empty-${i}`} className="calendar-day empty" />;
            }
            return (
              <button
                key={cell.dateStr}
                className={`calendar-day${isSelected(cell.dateStr) ? ' selected' : ''}${cell.hasStream ? ' has-stream' : ''}${!isCurrentMonth(cell.dateStr) ? ' other-month' : ''}`}
                onClick={() => cell.hasStream && onSelectDate(cell.dateStr)}
                disabled={!cell.hasStream}
                title={cell.hasStream ? `${cell.dateStr} - Available` : 'No stream data'}
              >
                {cell.day}
                {cell.hasStream && <span className="stream-dot" />}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Calendar;
