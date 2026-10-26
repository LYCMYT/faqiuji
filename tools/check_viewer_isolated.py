"""Validate this checkout on an ephemeral loopback port, not a stale server."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from functools import partial
import threading,subprocess,os,sys
from serve_viewer import Handler
R=Path(__file__).resolve().parents[1]
class QuietHandler(Handler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(R)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    subprocess.run([sys.executable,str(R/'tools/check_viewer.py')],cwd=R,env={**os.environ,'BM1_VIEWER_URL':f'http://127.0.0.1:{server.server_port}/viewer/'},check=True)
finally:server.shutdown();server.server_close();thread.join()
