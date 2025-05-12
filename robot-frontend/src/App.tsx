import { useState, useEffect } from "react";
import SetupForm from "./components/SetupForm";
import GridTable  from "./components/GridTable";
import { fetchGrid, nextTurn, robotView, type Grid } from "./api";

export default function App() {
  /** speed in auto mode ms */
  const autoSpeed = 300; 
  const [grid, setGrid] = useState<Grid | null>(null);
  const [discovered, setDiscovered] = useState(false);
  const [cleaned, setCleaned] = useState(false);
  const [auto, setAuto] = useState(false);

  const [numberIt, setnumberIt] = useState<number>(0);
  const [numberTrash, setnumberTrash] = useState<number>(0);
  /* ← 1.  callback from SetupForm  */
  const handleSuccess = (g: Grid) => setGrid(g);

  const refresh = async () => setGrid(await fetchGrid());
  const reset   = () => {
    setGrid(null);
    setAuto(false);
    setDiscovered(false);
    setCleaned(false);
    setnumberIt(0);
    setnumberTrash(0);
  };
  const next = async () => {
    const { grid, discovered, cleaned, num_it, num_trash } = await nextTurn();
    setGrid(grid);
    setDiscovered(discovered);
    setCleaned(cleaned);
    setnumberIt(num_it);
    setnumberTrash(num_trash);
  };

  const robot = async () => setGrid(await robotView());

  useEffect(() => {
    if (!auto || grid === null) return;

    const interval = setInterval(() => {
      next();
    }, autoSpeed);

    return () => clearInterval(interval); // clean up
  }, [auto, grid]);


  return (
    <>
      <h1>Robot Cleaner Express</h1>

      {/* ---- SETUP ---- */}
      {grid === null && (
        <SetupForm onSuccess={handleSuccess} />
      )}

      {/* ---- GRID ---- */}
      {grid !== null && (
        <>
          <div style={{ marginBottom: 4 }}>
            <button onClick={refresh} className="grid-button">
              Vue grille
            </button>
            <button onClick={robot} className="grid-button">
              Vue des robots
            </button>
            <button onClick={next} className="grid-button">
              Itérer
            </button>
           
            <button onClick={reset} className="grid-button">Relancer</button>
            <label className="grid-button">
              <input
                type="checkbox"
                checked={auto}
                onChange={(e) => setAuto(e.target.checked)}
              />{" "}
              Mode automatique
            </label>
          </div>
          <p>Nombre de tours: {numberIt}</p>
          <p style={{ marginBottom: 8 }}>Nombre de dechets: {numberTrash}</p>
          <GridTable grid={grid} />
          {/* finish messages */}
          {discovered && <p style={{ color: "green" }}>Toute la grille a été découverte par les robots !</p>}
          {cleaned && <p style={{ color: "blue" }}>La carte est totalement nettoyée !</p>}
        </>
      )}
    </>
  );
}