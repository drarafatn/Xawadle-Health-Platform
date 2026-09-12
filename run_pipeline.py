from pathlib import Path
from src.pipeline import export

if __name__ == '__main__':
    root=Path(__file__).parent
    output=root/'outputs'/'q3_analysis.json'
    export(root/'data', output)
    print(f'Wrote {output}')
