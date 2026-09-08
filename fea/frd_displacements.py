"""Strict ASCII CalculiX DISP extraction, preserving printed precision only."""
import math


def read(text, expected_nodes, selected_nodes):
    expected_nodes, selected_nodes = set(expected_nodes), set(selected_nodes)
    if not expected_nodes or not selected_nodes or not selected_nodes <= expected_nodes:
        raise ValueError("Require nonempty expected and selected node sets")
    result, rows, seen, labels, time, count = {}, None, set(), [], None, None
    for line in text.splitlines():
        if line.startswith("  100CL"):
            if rows is not None:
                raise ValueError("Unterminated DISP block")
            fields = line.split()
            time, count = float(fields[2]), int(fields[3])
            if not math.isfinite(time):
                raise ValueError("Nonfinite DISP time")
        elif line.startswith(" -4  DISP"):
            if time is None or time in result or rows is not None or count != len(expected_nodes):
                raise ValueError("Invalid DISP time/count")
            rows, seen, labels = {}, set(), []
        elif rows is not None:
            if line.startswith(" -5"):
                labels.append(line.split()[1])
            elif line.startswith(" -1"):
                node = int(line[3:13])
                values = [float(line[i:i+12]) for i in range(13, len(line), 12) if line[i:i+12].strip()]
                if node in seen or node not in expected_nodes or len(values) != 3 or not all(map(math.isfinite, values)):
                    raise ValueError("Invalid DISP node/vector")
                seen.add(node)
                if node in selected_nodes:
                    rows[node] = values
            elif line.startswith(" -3"):
                if labels != ["D1", "D2", "D3", "ALL"] or seen != expected_nodes:
                    raise ValueError("Incomplete DISP fields/nodes")
                result[time], rows = rows, None
            else:
                raise ValueError("Unexpected DISP record")
    if rows is not None or not result:
        raise ValueError("Missing or unterminated DISP output")
    return result
