import { useState } from "react";
import { setupGrid, type Grid } from "../api";
import GridSelector from "./GridSelector";

interface Props { onSuccess: (g: Grid) => void; }

interface Form { nr: number; nd: number; }   

const SIZE      = 32;
const CAPACITY  = SIZE * SIZE - 1;

export default function SetupForm({ onSuccess }: Props) {
  const [form, setForm] = useState<Form>({ nr: 5, nd: 20 });
  const [selected, setSelected] =
    useState<{ i: number; j: number } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const change = (k: keyof Form) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm({ ...form, [k]: Number(e.target.value) });

  /* validation client*/
  const validate = (): string | null => {
    if (!selected)       return "Cliquez dans la grille pour choisir le point de collected";
    if (form.nr < 1)     return "Au moins 1 robot";
    if (form.nd < 0)     return "Déchets ≥ 0";
    if (form.nr + form.nd > CAPACITY)
      return `Robots + déchets ≤ ${CAPACITY}`;
    return null;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const msg = validate();
    if (msg) { setErr(msg); return; }
    try {
      setLoading(true);
      const grid = await setupGrid({
        ...form,
        i: selected!.i,
        j: selected!.j,
      });
      onSuccess(grid);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <label>Nombre&nbsp;de&nbsp;robots&nbsp;(nr) : </label>
        <input type="number" min={1} size={2}
               value={form.nr} onChange={change("nr")} />
      </div>

      <div className="form-row">
        <label>Nombre&nbsp;de&nbsp;déchets&nbsp;(nd) : </label>
        <input type="number" min={0} size={2}
               value={form.nd} onChange={change("nd")} />
      </div>
      {selected && (
        <p>
          Position&nbsp;de collecte: (<strong>{selected.i}</strong>,
          <strong>{selected.j}</strong>)
        </p>
      )}
      <button className="formButton" type="submit" disabled={loading || !selected}>
        {loading ? "…" : "Initialiser"}
      </button>

      {err && <p style={{color:"red"}}>{err}</p>}

      <p>Choisissez la position de la <strong>collecte</strong> dans la grille :</p>
      <GridSelector
      selected={selected}
      onSelect={(i, j) => setSelected({ i, j })}
    />

    </form>
  );
}