import { BrowserRouter, Routes, Route } from "react-router-dom";

function HomePage() {
  return (
    <div>
      <h1>Sona AI OS</h1>
      <p>Welcome to the Sona AI dashboard.</p>
    </div>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
