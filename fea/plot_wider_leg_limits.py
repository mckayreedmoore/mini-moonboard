"""Render the saved conditional contact sensitivity; does not run the analysis."""
import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    source = Path('fea/results/wider-leg-limits.json')
    report = json.loads(source.read_text())
    half = report['assumptions']['foot_half_length_mm']
    fig, ax = plt.subplots(figsize=(9, 5.4), layout='constrained')
    ax.axvspan(-half/3, half/3, color='#dce9df', alpha=.8, label='Middle-third pressure range')
    for share, label, color in [('1.0', 'All rear load on one leg', '#9e3b32'),
                               ('0.5', 'Ideal equal sharing between legs', '#276584')]:
        curve = report['pressure_intervals_at_250_lb'][share]['conservative_lateral_plus_axial']['curve']
        ax.plot([p['offset_mm'] for p in curve], [p['ratio'] for p in curve],
                label=label, color=color, linewidth=2.4)
    ax.axhline(1, color='#343a40', linestyle='--', linewidth=1.2)
    ax.text(-half+2, 1.025, 'Design-reference limit', color='#343a40', fontsize=10)
    ax.set(xlim=(-half, half), ylim=(0, 2),
           xlabel='Pressure-resultant offset from foot center (mm)\n← Toward board     |     Away from board →',
           ylabel='Conservative lateral + axial ratio',
           title='Foot contact and load sharing dominate this connection screen')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.18)
    ax.legend(loc='upper center', fontsize=9, frameon=False)
    fig.supxlabel('250 lb × 2 downward + 300 N rearward; 25 kg equipment. Original conservative angle factors.\n'
                  'Conditional connection calculation only: edge geometry and prying remain unqualified.', fontsize=9)
    target = Path('docs/wider-leg-review/pressure-sensitivity')
    for extension in ('svg', 'png'):
        fig.savefig(target.with_suffix('.'+extension), dpi=180,
                    metadata={'Description': 'Source: '+str(source)} if extension == 'svg' else None)
    plt.close(fig)


if __name__ == '__main__':
    main()
