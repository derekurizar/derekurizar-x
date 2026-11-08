# Captura de métricas con Claude in Chrome (/analyze-improve)

Solo lectura: no se hace clic en nada que publique, edite, borre o acepte; no se descargan archivos. Todo corre en
**una pestaña nueva** del grupo MCP (cerrarla al terminar) con las sesiones que el usuario ya tiene abiertas. Si una
plataforma pide iniciar sesión, se salta y se dice en el reporte (nunca se escribe una contraseña).

**Cómo sale el JSON de Chrome**: la salida de `javascript_tool` se corta cerca de 1 KB. El fragmento de cada plataforma
deja el JSON en un `<textarea>` fijo arriba a la izquierda; luego `computer left_click (150, 60)` → `key cmd+a cmd+c` y
en Bash `pbpaste > sesiones/_analisis/<fecha>/captura_<plataforma>.json`. Comprueba con
`python3 -c "import json;json.load(open(...))"`. Un bucle largo (> 40 s) se lanza sin `await` (`(async()=>{…})()`) y se
consulta su bandera (`window.__done`) en otra llamada: así no se vence el límite de 45 s de `javascript_tool`.

Formato común (lo normaliza `scripts/metricas.py importar`; los números pueden ir como texto «3,184», «39K», «5.6%»):

```json
{"plataforma": "tiktok|youtube|instagram|facebook", "fecha": "AAAA-MM-DD",
 "publicaciones": [{"post_id": "…", "url": "…", "titulo": "…", "fecha_pub": "AAAA-MM-DDTHH:MM", "duracion_s": 172,
   "views": "37K", "likes": 675, "comments": 26, "shares": 127, "saves": 254, "follows": 35, "avg_s": 44.2,
   "completion": "10.5%", "viewed_pct": "70.1%", "views_3s": 96, "views_1m": 14, "distribucion": "+1.1",
   "trafico": {"para_ti": "98.7%"}, "curva": [1, 0.85, 0.74]}]}
```

## TikTok Studio (`https://www.tiktok.com/tiktokstudio/content?lang=es`)

1. **Lista** (scroll virtual: se acumula mientras baja). Columnas: duración · título · fecha («3 nov, 15:02» o
   «16 oct 2025, 11:09») · privacidad · vistas · me gusta · comentarios.

```js
await new Promise(r=>setTimeout(r,3000));
const MES={ene:1,feb:2,mar:3,abr:4,may:5,jun:6,jul:7,ago:8,sept:9,sep:9,oct:10,nov:11,dic:12};
const ANIO=String(new Date().getFullYear());
function fecha(s){const m=s.match(/(\d+) (\w+)\.?(?: (\d{4}))?, (\d+:\d+)/); if(!m) return ''; return (m[3]||ANIO)+'-'+String(MES[m[2].toLowerCase()]).padStart(2,'0')+'-'+m[1].padStart(2,'0')+'T'+m[4].padStart(5,'0');}
function dur(s){const [a,b]=s.split(':').map(Number); return a*60+b;}
window.__lst={};
const sc=[...document.querySelectorAll('*')].filter(e=>e.scrollHeight>e.clientHeight+50 && /auto|scroll/.test(getComputedStyle(e).overflowY));
for(let i=0;i<45;i++){
 document.querySelectorAll('a[href*="/video/"]').forEach(a=>{let r=a; for(let k=0;k<8&&r.parentElement;k++){ r=r.parentElement; if(r.innerText && r.innerText.split('\n').length>6) break;}
   const t=r.innerText.split('\n').filter(Boolean); const id=a.href.split('/').pop();
   if(!window.__lst[id]) window.__lst[id]={post_id:id,url:a.href,duracion_s:dur(t[0]),titulo:t[1],fecha_pub:fecha(t[2]),views:t[4],likes:t[5],comments:t[6]};});
 for(const s of sc) s.scrollTop+=400; window.scrollBy(0,400); await new Promise(r=>setTimeout(r,600));
}
Object.keys(window.__lst).length
```

2. **Analítica por video** (en un iframe del mismo origen; la curva de retención por segundo está en los props de
   React del gráfico: `data = [{x: "0", y: 1}, {x: "1000", y: 0.83}, …]`). Solo las publicaciones desde `desde`.

```js
async function grab(id){
 const fr=document.createElement('iframe'); fr.style.cssText='width:1400px;height:3000px;position:fixed;left:-5000px;top:0';
 fr.src='/tiktokstudio/analytics/'+id+'?lang=es'; document.body.appendChild(fr); let res=null;
 for(let t=0;t<40 && !res;t++){ await new Promise(r=>setTimeout(r,800));
  try{ const d=fr.contentDocument;
   for(const c of d.querySelectorAll('canvas')){ let p=c,key; while(p && !(key=Object.keys(p).find(k=>k.startsWith('__reactFiber')))) p=p.parentElement; if(!p) continue;
     let f=p[key],dep=0; while(f&&dep<10){const pr=f.memoizedProps; if(pr&&Array.isArray(pr.data)&&pr.data[0]&&pr.data[0].x==='0'&&pr.data.length>5){res={curva:pr.data.map(o=>o.y)};break;} f=f.return;dep++;} if(res) break; }
   if(res){ const tx=d.body.innerText.replace(/\n+/g,'\n'); const g=re=>{const m=tx.match(re); return m?m[1]:null;};
     const top=tx.slice(tx.indexOf('Publicado el')).split('\n').slice(1,6);
     Object.assign(res,{views:top[0],likes:top[1],comments:top[2],shares:top[3],saves:top[4]});
     const avg=g(/promedio de visualización\n([^\n]+)/);
     res.avg_s=avg?(avg.includes(':')?(()=>{const q=avg.replace('s','').split(/[:hm]/).map(Number);return q.length==2?q[0]*60+q[1]:q[0];})():parseFloat(avg)):null;
     res.completion=g(/vídeo completo\n([\d.,]+%)/); res.follows=g(/Nuevos seguidores\n(\d+)/);
     const pt=g(/Para ti\n([\d.<]+%)/); res.trafico=pt?{para_ti:pt.replace('<','')}:{}; } }catch(e){} }
 fr.remove(); return res; }
window.__an={}; const DESDE='2026-10-19';   // ← el `desde` del comando
const ids=Object.values(window.__lst).filter(x=>x.fecha_pub>=DESDE).map(x=>x.post_id);
(async()=>{ for(const id of ids) window.__an[id]=await grab(id); window.__done=true; })(); 'started '+ids.length
```

3. **Volcar** (cuando `window.__done`): el textarea con
   `{plataforma:'tiktok', fecha, publicaciones: lista ⊕ analítica}`.

```js
const pubs=Object.values(window.__lst).map(x=>{const a=window.__an[x.post_id]||{}; return Object.assign({},x,a,{views:a.views||x.views,likes:a.likes||x.likes,comments:a.comments||x.comments});});
const ta=document.createElement('textarea'); ta.value=JSON.stringify({plataforma:'tiktok',fecha:new Date().toISOString().slice(0,10),publicaciones:pubs});
ta.style.cssText='position:fixed;top:10px;left:10px;width:300px;height:100px;z-index:999999'; document.body.appendChild(ta); ta.value.length
```

## YouTube Studio (`https://studio.youtube.com/channel/<id>/videos/short`)

La URL `/channel/UC/videos/short` redirige al canal propio. Lista de Shorts (`ytcp-video-row`), luego la vista general
de cada uno en un iframe: «Se quedaron viendo N %» (visto frente a deslizado) y «Duración media de las visualizaciones».
Lento (≈ 4 s por Short): lanzar sin `await`. Un Short con pocas vistas se revisa en `/video/<id>/edit` («Debes
responder a esta pregunta» en Audiencia = la subida quedó sin la pregunta «hecho para niños» y no se distribuye).

```js
await new Promise(r=>setTimeout(r,4000));
const MES={ene:1,feb:2,mar:3,abr:4,may:5,jun:6,jul:7,ago:8,sept:9,sep:9,oct:10,nov:11,dic:12};
window.__yl=[...document.querySelectorAll('ytcp-video-row')].map(r=>{const a=r.querySelector('a[href*="/video/"]'); const id=a.href.match(/video\/([^/]+)/)[1];
 const t=r.innerText.split('\n').map(s=>s.trim()).filter(Boolean); const d=t.find(s=>/^\d+ \w+ \d{4}$/.test(s))||''; const m=d.split(' '); const di=t.indexOf(d); const [mm,ss]=t[0].split(':').map(Number);
 return {post_id:id,url:'https://youtube.com/shorts/'+id,titulo:t[1],duracion_s:mm*60+ss,fecha_pub:m.length==3?m[2]+'-'+String(MES[m[1]]).padStart(2,'0')+'-'+m[0].padStart(2,'0'):'',views:t[di+2],comments:t[di+3]};});
window.__ya={};
async function grab(id){ const fr=document.createElement('iframe'); fr.style.cssText='width:1400px;height:2500px;position:fixed;left:-5000px;top:0';
 fr.src='/video/'+id+'/analytics/tab-overview/period-default'; document.body.appendChild(fr); let out=null;
 for(let t=0;t<30&&!out;t++){ await new Promise(r=>setTimeout(r,1000)); try{ const tx=fr.contentDocument.body.innerText;
   const m=tx.match(/Se quedaron viendo\s*([\d,.]+)\s*%/), a=tx.match(/Duración media de las visualizaciones\s*(\d+):(\d+)/);
   if(m&&a) out={viewed_pct:m[1].replace(',','.')+'%',avg_s:Number(a[1])*60+Number(a[2])}; }catch(e){} }
 fr.remove(); return out; }
(async()=>{ for(const x of window.__yl) window.__ya[x.post_id]=await grab(x.post_id); window.__ydone=true; })(); window.__yl.length
```

Volcar: `publicaciones = __yl ⊕ __ya` en el textarea (como en TikTok), `plataforma: 'youtube'`.

## Facebook (`https://www.facebook.com/professional_dashboard/content/content_library`)

Tabla de la Biblioteca de contenido (últimos 30 días). Columnas tras «Published •» y la fecha: Views · Viewers ·
Engagement · Net follows · Impressions · Comments · Distribution · Watch time · Average watch time · 3-second views ·
1-minute views. No muestra el id ni la duración: `post_id` = la fecha y hora (AAAAMMDDHHMM); `vincular` usa fecha y
título. Las horas traen espacios finos (` `) antes de AM/PM.

```js
await new Promise(r=>setTimeout(r,5000));
const MES={Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
function fecha(s){ const hoy=new Date(); let d; const m=s.replace(/[  ]/g,' ').match(/(Today|Yesterday|(\w{3}) (\d+)) at (\d+):(\d+)\s*(AM|PM)/); if(!m) return '';
 if(m[1]=='Today') d=new Date(hoy); else if(m[1]=='Yesterday'){d=new Date(hoy); d.setDate(d.getDate()-1);} else d=new Date(hoy.getFullYear(),MES[m[2]]-1,Number(m[3]));
 const h=Number(m[4])%12+(m[6]=='PM'?12:0); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')+'T'+String(h).padStart(2,'0')+':'+m[5]; }
function secs(s){ if(!s||/‑‑|--/.test(s)) return null; let t=0; (s.match(/\d+[hms]/g)||[]).forEach(p=>{const v=parseInt(p); t+=p.endsWith('h')?v*3600:p.endsWith('m')?v*60:v;}); return t; }
const filas=new Map(); const sc=[...document.querySelectorAll('*')].filter(e=>e.scrollHeight>e.clientHeight+80 && /auto|scroll/.test(getComputedStyle(e).overflowY));
for(const s of sc) s.scrollTop=0; await new Promise(r=>setTimeout(r,1000));
for(let i=0;i<25;i++){ const L=document.body.innerText.split('\n');
 for(let j=0;j<L.length;j++) if(/^Published/.test(L[j]) && /(Today|Yesterday| at \d)/.test(L[j+1]||'')){ let k=j-1; while(k>0&&!L[k].trim()) k--; const v=L.slice(j+2,j+13); const f=fecha(L[j+1]);
   if(!filas.has(f) && !/^(Photo story|No text content)/.test(L[k])) filas.set(f,{post_id:f.replace(/\D/g,''),url:'',titulo:L[k],fecha_pub:f,views:v[0],likes:v[2],follows:v[3],comments:v[5],distribucion:(v[6]||'').replace('x',''),avg_s:secs(v[8]),views_3s:v[9],views_1m:v[10]}); }
 for(const s of sc) s.scrollTop+=400; await new Promise(r=>setTimeout(r,800)); }
const ta=document.createElement('textarea'); ta.value=JSON.stringify({plataforma:'facebook',fecha:new Date().toISOString().slice(0,10),publicaciones:[...filas.values()]});
ta.style.cssText='position:fixed;top:10px;left:10px;width:300px;height:100px;z-index:999999'; document.body.appendChild(ta); filas.size
```

## Instagram (`https://www.instagram.com/accounts/insights/content/?media_type=all&metric=accounts_engaged&sort_by=highest&timeframe=30&view_type=card`)

La cuadrícula no expone ids. Se abre cada tarjeta con un clic por JS (`img → 3 padres → click()`), se lee
`/insights/media/<id>/` (Visualizaciones, Espectadores, Me gusta, Comentarios, Veces que se ha guardado, Veces que se ha
compartido, Seguidores) y se vuelve con `history.back()`; caption, fecha y duración salen de la API web del mismo origen
(`/api/v1/media/<id>/info/` con la cabecera `x-ig-app-id: 936619743392459`). La web no da curva ni tiempo medio de los
reels: Instagram aporta vistas, guardados, compartidos y seguidores.

```js
window.__ig=[];
(async()=>{ for(let i=0;i<20;i++){
  for(let t=0;t<20 && document.querySelectorAll('main img').length<=i;t++) await new Promise(r=>setTimeout(r,500));
  const img=document.querySelectorAll('main img')[i]; if(!img) break; let p=img; for(let k=0;k<3;k++) p=p.parentElement; p.click();
  let tx=''; for(let t=0;t<20;t++){ await new Promise(r=>setTimeout(r,500)); if(/insights\/media\/\d+/.test(location.href) && /Veces que se ha compartido/.test(document.body.innerText)){ tx=document.body.innerText; break; } }
  window.__ig.push({id:(location.href.match(/media\/(\d+)/)||[])[1], tx:tx.slice(0,1200)}); history.back(); await new Promise(r=>setTimeout(r,2500)); }
 window.__igdone=true; })(); 'started'
```

Luego, con `window.__igdone`:

```js
const g=(tx,re)=>{const m=tx.match(re); return m?m[1]:null;};
const pubs=[]; for(const x of window.__ig.filter(x=>x.id)){
 const info=await fetch('/api/v1/media/'+x.id+'/info/',{headers:{'x-ig-app-id':'936619743392459'},credentials:'include'}).then(r=>r.json()).catch(()=>({}));
 const it=(info.items||[])[0]||{};
 const ts=it.taken_at? new Date(it.taken_at*1000-6*3600*1000): null;   // hora de Guatemala (UTC−6)
 pubs.push({post_id:x.id, url: it.code?'https://www.instagram.com/reel/'+it.code+'/':'', titulo:((it.caption||{}).text||'').split('\n')[0].slice(0,150),
   fecha_pub: ts? ts.toISOString().slice(0,16):'', duracion_s: it.video_duration||null,
   views:g(x.tx,/Visualizaciones\n([\d.,]+)/), likes:g(x.tx,/Me gusta\n([\d.,]+)/), comments:g(x.tx,/Comentarios\n([\d.,]+)/),
   saves:g(x.tx,/guardado\n([\d.,]+)/), shares:g(x.tx,/compartido\n([\d.,]+)/), follows:g(x.tx,/Seguidores\n(\d+)\n/)}); }
const ta=document.createElement('textarea'); ta.value=JSON.stringify({plataforma:'instagram',fecha:new Date().toISOString().slice(0,10),publicaciones:pubs});
ta.style.cssText='position:fixed;top:10px;left:10px;width:300px;height:100px;z-index:999999'; document.body.appendChild(ta); pubs.length
```

Instagram usa el punto como separador de miles («28.282»): `metricas.py` lo lee bien. `taken_at` está en UTC; el
fragmento le resta 6 h (Guatemala) para que la fecha y la hora sean las locales.
