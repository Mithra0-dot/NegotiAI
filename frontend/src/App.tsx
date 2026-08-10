import { useState } from "react";
import { ScenarioPicker } from "./components/ScenarioPicker";
import type { Scenario } from "./types/scenario";

function App() {
  // Session creation / chat screen is a later feature — for now, selecting
  // a scenario just stores it so we can see the picker responding.
  const [selected, setSelected] = useState<Scenario | null>(null);

  return (
    <>
      <ScenarioPicker onSelect={setSelected} />
      {selected && (
        <p className="pb-16 text-center text-sm text-slate-500">
          Selected: {selected.name} (session start not built yet)
        </p>
      )}
    </>
  );
}

export default App;
