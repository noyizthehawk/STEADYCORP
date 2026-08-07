import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Lookbook from "./pages/Lookbook";
import SignIn from "./pages/SignIn";
import Store from "./pages/Store";

// The whole route map. Layout wraps every page (shared header + <Outlet/>).
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/store" element={<Store />} />
        <Route path="/lookbook" element={<Lookbook />} />
        <Route path="/signin" element={<SignIn />} />
      </Route>
    </Routes>
  );
}
