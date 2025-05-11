// src/components/GridSelector.tsx
interface Props {
    selected: { i: number; j: number } | null;
    onSelect: (i: number, j: number) => void;
  }
  
  const SIZE = 32;
  
  export default function GridSelector({ selected, onSelect }: Props) {
    return (
      <table style={{ borderCollapse: "collapse", marginTop: 12 }}>
        <tbody>
          {Array.from({ length: SIZE }, (_, i) => (
            <tr key={i}>
              {Array.from({ length: SIZE }, (_, j) => {
                const isSel = selected?.i === i && selected?.j === j;
                return (
                  <td
                    key={j}
                    onClick={() => onSelect(i, j)}
                    className={`grid-cell grid-select ${isSel ? "trash-cell" : ""}`}
                    title={`(${i},${j})`}
                  />
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }