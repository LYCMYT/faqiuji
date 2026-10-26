"""Windows-safe local server: explicit JavaScript MIME, loopback only."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import os,sys,threading,webbrowser,argparse
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'application/javascript','.mjs':'application/javascript','.glb':'model/gltf-binary','.json':'application/json','.svg':'image/svg+xml'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);ap.add_argument('--open',action='store_true');ap.add_argument('--revision',choices=['R1','R3','R4'],default='R4');args=ap.parse_args()
    os.chdir(Path(__file__).resolve().parents[1]);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    entry={'R1':'viewer/','R3':'output/fixture_r3/viewer.html','R4':'output/fixture_r4/viewer.html'}[args.revision]
    url=f'http://127.0.0.1:{server.server_port}/'+entry
    print('BM1 viewer: '+url,flush=True)
    if args.open:threading.Timer(.5,lambda:webbrowser.open(url)).start()
    server.serve_forever()
