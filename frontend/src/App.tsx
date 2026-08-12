import { Route, Routes } from "react-router-dom";
import { ChatPage } from "./pages/ChatPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ScenarioPickerPage } from "./pages/ScenarioPickerPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<ScenarioPickerPage />} />
      <Route path="/chat/:scenarioId" element={<ChatPage />} />
      <Route path="/history" element={<HistoryPage />} />
    </Routes>
  );
}

export default App;
