import { Route, Routes } from "react-router-dom";
import { ChatPage } from "./pages/ChatPage";
import { ScenarioPickerPage } from "./pages/ScenarioPickerPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<ScenarioPickerPage />} />
      <Route path="/chat/:scenarioId" element={<ChatPage />} />
    </Routes>
  );
}

export default App;
