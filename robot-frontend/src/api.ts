const BASE = "http://localhost:8000/api";           // backend robots using django 

export interface SetupPayload {
  nr: number;
  nd: number;
  i: number;
  j: number;
}
/* 0: Empty, U: unknown, R: Robot, D: Disposal (garbage) , xL : x Locked in robot view */
export type Cell = "0" | "U" | "R" | "D" | "Z"  | "RL" | "DL" | "UL";
export type Grid = Cell[][];
export interface NextTurnResponse {
  grid: Grid;
  discovered: boolean;
  cleaned: boolean;
  num_it: number;
  num_trash: number;
}

/* POST /api/setup/ ------------------------------------------------------ */
export async function setupGrid(payload: SetupPayload): Promise<Grid> {
  const res = await fetch(`${BASE}/setup/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Setup: ${res.status} ${res.statusText}`);
  return (await res.json()).grid as Grid;
}

/* GET /api/grid/ -------------------------------------------------------- */
export async function fetchGrid(): Promise<Grid> {
  const res = await fetch(`${BASE}/grid/`);
  if (!res.ok) throw new Error(`Grid : ${res.status} ${res.statusText}`);
  return (await res.json()).grid as Grid;
}

/* GET /api/next/ -------------------------------------------------------- */
export async function nextTurn(): Promise<NextTurnResponse> {
  const res = await fetch(`${BASE}/next/`);
  if (!res.ok) throw new Error(`nextTurn : ${res.status} ${res.statusText}`);
  return (await res.json()) as NextTurnResponse;
}

/* GET /api/robot/ -------------------------------------------------------- */
export async function robotView(): Promise<Grid> {
  const res = await fetch(`${BASE}/robot/`);
  if (!res.ok) throw new Error(`robotView : ${res.status} ${res.statusText}`);
  return (await res.json()).grid as Grid;
}
