import { Link } from "react-router-dom";
import { useState, useEffect } from "react";

// TODO: swap in your real Instagram handle
const INSTAGRAM_URL = "https://instagram.com/steadyincorp";

// The plain entry page: two ways in.
export default function Landing() {

    const [time, setTime] = useState<Date>(new Date());
  
    useEffect(() => {
      const timer = setInterval(() => {
        setTime(new Date());
      }, 1000);
  
      // Cleans up the timer when the component disappears
      return () => clearInterval(timer);
    }, []);
  
    // Formats the output strictly to Mountain Time
    const mountainTime = time.toLocaleTimeString('en-US', {
      timeZone: 'America/Edmonton', // Uses Mountain Time Zone
      hour12: true,                 // Displays AM/PM
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  
  return (
    <nav className="flex flex-col items-center gap-6">
      <div>{mountainTime} MT </div>
      <Link to="/store" className="lnk">
        RECEPTIONIST
      </Link>
      <Link to="/lookbook" className="lnk">
        LOOKBOOK
      </Link>
      <a
        href={INSTAGRAM_URL}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Instagram"
        className="lnk"
      >
        <svg
          viewBox="0 0 24 24"
          width="24"
          height="24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <rect x="2" y="2" width="20" height="20" rx="5" />
          <circle cx="12" cy="12" r="4" />
          <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
        </svg>
      </a>
    </nav>
  );
}
