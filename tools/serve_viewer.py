"""Windows-safe local server: explicit JavaScript MIME, loopback only."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import os,sys,threading,webbrowser,argparse
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'application/javascript','.mjs':'application/javascript','.glb':'model/gltf-binary','.json':'application/json','.svg':'image/svg+xml'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);ap.add_argument('--open',action='store_true');args=ap.parse_args()
    os.chdir(Path(__file__).resolve().parents[1]);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    url=f'http://127.0.0.1:{server.server_port}/viewer/'
    print('BM1 viewer: '+url,flush=True)
    if args.open:threading.Timer(.5,lambda:webbrowser.open(url)).start()
    server.serve_forever()
