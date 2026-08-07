import { Link } from "react-router-dom";

// The plain entry page: two ways in.
export default function Landing() {
  return (
    <nav className="flex flex-col items-center gap-6">
      <Link to="/store" className="lnk">
        RECEPTIONIST
      </Link>
      <Link to="/lookbook" className="lnk">
        LOOKBOOK
      </Link>
    </nav>
  );
}
