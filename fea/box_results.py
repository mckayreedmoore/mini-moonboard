"""Validate CalculiX displacement and global force-balance output."""
import math
import re


def parse_results(data, cases):
    blocks=re.findall(r"displacements[^\n]*\n(.*?)(?=\n\s*[^\s\d.+-]|\Z)",data,re.DOTALL|re.IGNORECASE)
    maxima=[]
    for block in blocks:
        vectors=[]
        for line in block.splitlines():
            cells=line.split()
            if len(cells)==4 and cells[0].isdigit():
                vectors.append([float(v) for v in cells[1:]])
        if len(vectors)!=5 or not all(math.isfinite(v) for xyz in vectors for v in xyz):
            raise ValueError("Expected five finite top-node vectors in every case")
        maxima.append(max(math.sqrt(sum(v*v for v in xyz)) for xyz in vectors))
    reaction_lines=re.findall(r"total force[^\n]*\n\s*\n\s*([^\n]+)",data,re.IGNORECASE)
    reactions=[[float(v) for v in line.split()] for line in reaction_lines]
    if len(maxima)!=len(cases) or len(reactions)!=len(cases):
        raise ValueError("Missing displacement or reaction case")
    for (name,force),reaction in zip(cases,reactions,strict=True):
        if len(reaction)!=3 or any(not math.isfinite(r) or abs(r+1200*f)>.1 for r,f in zip(reaction,force,strict=True)):
            raise ValueError(f"Unbalanced reaction: {name}")
    return dict(zip([name for name,_ in cases],maxima,strict=True)),reactions
