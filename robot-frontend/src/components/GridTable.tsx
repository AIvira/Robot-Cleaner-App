import { type Grid } from "../api";

interface Props { grid: Grid; }

export default function GridTable({ grid }: Props) {
  return (
    <div className="overflow-auto max-h-[80vh]">
      <table className="border-collapse">
        <tbody>
          {grid.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}
                  className={`grid-cell 
                  ${(cell === "R" || cell === "RL") ? "robot-cell" :
                    (cell === "D" || cell === "DL") ? "garbage-cell" :
                    cell === "Z" ? "trash-cell" : 
                    (cell === "U" || cell === "UL") ? "unknown-cell" : ""} 
                    
                    ${(cell.endsWith('L')) ? "locked-cell" : ""}`
                  }>
                  </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
