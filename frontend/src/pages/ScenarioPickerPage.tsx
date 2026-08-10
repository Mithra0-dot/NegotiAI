import { useNavigate } from "react-router-dom";
import { ScenarioPicker } from "../components/ScenarioPicker";
import type { Scenario } from "../types/scenario";

export function ScenarioPickerPage() {
  const navigate = useNavigate();

  function handleSelect(scenario: Scenario) {
    navigate(`/chat/${scenario.id}`);
  }

  return <ScenarioPicker onSelect={handleSelect} />;
}
