from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from socketserver import ThreadingUDPServer,BaseRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
import json,uuid,time,threading,socket,struct,argparse,mimetypes,html
R=Path(__file__).resolve().parent; (R/'sites/hello').mkdir(parents=True,exist_ok=True);(R/'data').mkdir(exist_ok=True); DB=R/'data/xnet.json'; L=threading.Lock()
def db():
 if not DB.exists():
  d={'node_id':'xnode-'+uuid.uuid4().hex[:8],'domains':{'hello.xnet':'hello'},'sites':{'hello':{'title':'Hello XNet','description':'Первый сайт XNet'}},'peers':[]};DB.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d
 return json.loads(DB.read_text('utf-8'))
def save(d):
 with L:DB.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf-8')
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,c,x,t='application/json; charset=utf-8'):
  b=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False).encode() if not isinstance(x,str) else x.encode());self.send_response(c);self.send_header('Content-Type',t);self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
 def read(self):
  n=int(self.headers.get('Content-Length',0));return json.loads(self.rfile.read(min(n,1000000)) or b'{}')
 def do_GET(self):
  p=urlparse(self.path);d=db()
  if p.path=='/':return self.send(200,(R/'index.html').read_bytes(),'text/html; charset=utf-8')
  if p.path in ['/app.js','/styles.css']:return self.send(200,(R/p.path[1:]).read_bytes(),'text/javascript' if p.path.endswith('.js') else 'text/css')
  if p.path=='/api/status':return self.send(200,{'ok':True,'version':'0.1.0','node_id':d['node_id'],'sites':len(d['sites']),'domains':len(d['domains']),'peers':len(d['peers'])})
  if p.path=='/api/sites':return self.send(200,d['sites'])
  if p.path=='/api/domains':return self.send(200,d['domains'])
  if p.path=='/api/peers':return self.send(200,d['peers'])
  if p.path=='/api/search':
   q=parse_qs(p.query).get('q',[''])[0].lower();return self.send(200,[{'domain':dm,'title':d['sites'].get(sl,{}).get('title',sl),'description':d['sites'].get(sl,{}).get('description',''),'url':'/site/'+sl} for dm,sl in d['domains'].items() if q in (dm+str(d['sites'].get(sl,{}))).lower()])
  if p.path.startswith('/site/'):
   a=p.path.split('/',3);slug=a[2];f=(R/'sites'/slug/(a[3] if len(a)>3 else 'index.html')).resolve()
   if R.joinpath('sites').resolve() not in f.parents or not f.is_file():return self.send(404,'Not found','text/plain')
   return self.send(200,f.read_bytes(),mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  return self.send(404,'Not found','text/plain')
 def do_POST(self):
  try:x=self.read()
  except:return self.send(400,{'error':'Invalid JSON'})
  d=db();p=urlparse(self.path).path
  if p=='/api/sites':
   s=str(x.get('slug','')).lower().strip();title=str(x.get('title','New site'))[:80];desc=str(x.get('description',''))[:240]
   if not s or len(s)>40 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in s):return self.send(400,{'error':'Slug: латиница, цифры, дефис'})
   folder=R/'sites'/s;folder.mkdir(exist_ok=True);(folder/'index.html').write_text(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>body{{background:#0b0b12;color:#eee;font:18px system-ui;padding:12vh 10vw}}h1{{color:#a99aff}}</style><h1>{html.escape(title)}</h1><p>{html.escape(desc)}</p><small>XNet Web · {s}</small>','utf-8');d['sites'][s]={'title':title,'description':desc};save(d);return self.send(201,{'ok':True,'url':'/site/'+s})
  if p=='/api/domains':
   dm=str(x.get('domain','')).lower().strip();s=x.get('slug','')
   if not dm.endswith('.xnet') or s not in d['sites']:return self.send(400,{'error':'Укажи домен .xnet и существующий сайт'})
   d['domains'][dm]=s;save(d);return self.send(201,{'ok':True})
  if p=='/api/peers':
   a=str(x.get('address','')).strip()
   if not a.startswith(('http://','https://')):return self.send(400,{'error':'Нужен URL http:// или https://'})
   d['peers'].append({'id':uuid.uuid4().hex[:8],'address':a});save(d);return self.send(201,{'ok':True})
  return self.send(404,{'error':'Unknown endpoint'})
 def do_DELETE(self):
  d=db();p=urlparse(self.path).path
  if p.startswith('/api/domains/'):d['domains'].pop(unquote(p.split('/')[-1]),None)
  elif p.startswith('/api/peers/'):d['peers']=[x for x in d['peers'] if x['id']!=p.split('/')[-1]]
  else:return self.send(404,{'error':'Not found'})
  save(d);return self.send(200,{'ok':True})
class DNS(BaseRequestHandler):
 def handle(self):
  b,sock=self.request
  try:
   pos=12;labels=[]
   while b[pos]:n=b[pos];pos+=1;labels.append(b[pos:pos+n].decode());pos+=n
   pos+=1;qt,qc=struct.unpack('!HH',b[pos:pos+4]);q=b[12:pos+4];found='.'.join(labels).lower() in db()['domains'];ans=b'\xc0\x0c'+struct.pack('!HHIH',1,1,60,4)+socket.inet_aton(self.server.ip) if found and qt in (1,255) else b''
   sock.sendto(b[:2]+struct.pack('!HHHHH',0x8180,1,1 if ans else 0,0,0)+q+ans,self.client_address)
  except:pass
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--host',default='0.0.0.0');ap.add_argument('--port',type=int,default=8080);ap.add_argument('--dns-port',type=int,default=5353);ap.add_argument('--no-dns',action='store_true');a=ap.parse_args();ip=socket.gethostbyname(socket.gethostname());srv=ThreadingHTTPServer((a.host,a.port),H);print(f'XNet Control Center: http://127.0.0.1:{a.port} | LAN IP: {ip}:{a.port}')
 if not a.no_dns:
  try:d=ThreadingUDPServer((a.host,a.dns_port),DNS);d.ip=ip;threading.Thread(target=d.serve_forever,daemon=True).start();print(f'XDNS UDP :{a.dns_port} (test mode)')
  except OSError as e:print('DNS start failed:',e)
 try:srv.serve_forever()
 except KeyboardInterrupt:pass
if __name__=='__main__':main()
