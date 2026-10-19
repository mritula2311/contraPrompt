"""Build a source ZIP with a complete file manifest; exclude private runtime state."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def files():
    excluded={'__pycache__','.pytest_cache','.venv','.git'}
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in excluded or x.startswith('live_') for x in p.relative_to(ROOT).parts) and p.name!='.env' and p.suffix not in ('.pyc','.sqlite3','.zip'))
def package(output):
    output=Path(output).resolve()
    (ROOT/'TREE.txt').write_text('ContradictPrompt/\n'+'\n'.join('  '+str(p.relative_to(ROOT)) for p in files())+'\n')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files() if p.name!='FILE_MANIFEST.json'}
    (ROOT/'FILE_MANIFEST.json').write_text(json.dumps({'version':'1.0.1','sha256':manifest},indent=2))
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files(): z.write(p,'ContradictPrompt/'+str(p.relative_to(ROOT)))
    with zipfile.ZipFile(output) as z: assert z.testzip() is None
    print(f'Packaged {len(files())} files: {output}')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',nargs='?',default=str(ROOT.parent/'ContradictPrompt.zip'));a=p.parse_args();package(a.output)
