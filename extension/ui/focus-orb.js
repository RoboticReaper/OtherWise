// Adapted from BowenX307/otherwise@8281161 src/universe/orbCore.ts.
// Orb owns SVG primitives only; the scene supplies its sole animation clock.
const NS='http://www.w3.org/2000/svg';
export const ORB_UNITS=100;
const GAP=9, FLARE=1.4, ROUND=4;
const STATES={
  whole:{breathe:.01,slit:()=>({angle:0,offset:0,width:0})},
  sleep:{breathe:.02,slit:t=>({angle:Math.sin(t*.25)*3,offset:0,width:GAP*.45})},
  idle:{breathe:.012,slit:t=>({angle:Math.sin(t*.7)*6,offset:Math.sin(t*.9)*8,width:GAP*(.9+.15*Math.sin(t*1.3))})},
  look:{breathe:.012,slit:(t,look)=>({angle:look+Math.sin(t*1.3)*2,offset:0,width:GAP})},
  greet:{breathe:.015,slit:t=>({angle:Math.sin(t*.8)*4,offset:0,width:GAP*(2.1+.25*Math.sin(t*3))})},
  reading:{breathe:.008,slit:t=>({angle:Math.sin(t*1.6)*22,offset:0,width:GAP})},
  release:{breathe:0,slit:()=>({angle:0,offset:0,width:GAP*4.2})},
};
const lerp=(a,b,k)=>a+(b-a)*k;
function slitPath(w,d) {
  if(w<=.01)return '';
  const L=Math.sqrt(Math.max(ORB_UNITS**2-d*d,400));
  const half=x=>(w/2)*(1+FLARE*Math.min(1,(x/L)**2));
  const top=[],bottom=[];
  for(let i=0;i<=16;i++){
    const x=-L+2*L*i/16;
    top.push(`${x.toFixed(1)},${(-half(x)).toFixed(2)}`);
    bottom.unshift(`${x.toFixed(1)},${half(x).toFixed(2)}`);
  }
  const end=w/2*(1+FLARE),ext=L+60;
  return `M${-ext},${-end} L${top.join(' L')} L${ext},${-end} L${ext},${end} L${bottom.join(' L')} L${-ext},${end}Z`;
}
function el(tag,attrs,parent){
  const node=document.createElementNS(NS,tag);
  for(const [key,value]of Object.entries(attrs))node.setAttribute(key,String(value));
  parent.append(node);return node;
}
const threshold=at=>`1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 ${.5-20*at}`;
export class OrbCore {
  constructor(parent,defs,{idPrefix,color='#eee9de'}) {
    const id=String(idPrefix).replace(/[^a-zA-Z0-9_-]/g,'-');
    this.cur={angle:0,offset:0,width:0};this.state='whole';this.look=0;this.t=0;this.breathe=0;this.squeeze=1;
    const round=el('filter',{id:`${id}-round`,filterUnits:'userSpaceOnUse',x:-130,y:-130,width:260,height:260},defs);
    el('feGaussianBlur',{stdDeviation:ROUND},round);el('feColorMatrix',{type:'matrix',values:threshold(.85)},round);
    el('feGaussianBlur',{stdDeviation:ROUND},round);el('feColorMatrix',{type:'matrix',values:threshold(.15)},round);
    const mask=el('mask',{id:`${id}-slit`,maskUnits:'userSpaceOnUse',x:-130,y:-130,width:260,height:260},defs);
    el('rect',{x:-130,y:-130,width:260,height:260,fill:'#fff'},mask);
    this.slitEl=el('path',{fill:'#000'},mask);
    this.body=el('g',{filter:`url(#${id}-round)`},parent);
    this.circle=el('circle',{r:ORB_UNITS,fill:color,mask:`url(#${id}-slit)`},this.body);
    this.nodes=[round,mask,this.body];
  }
  destroy(){this.nodes.forEach(node=>node.remove());}
  setState(state){this.state=STATES[state]?state:'idle';}
  setLook(deg){this.look=Number.isFinite(deg)?deg:0;}
  setSqueeze(value){this.squeeze=value;}
  update(dt,reduced){
    this.t+=reduced?0:dt;
    const st=STATES[this.state],k=reduced?1:1-Math.exp(-dt*(this.state==='release'?14:6));
    const target=st.slit(this.t,this.look),n=Math.round((this.cur.angle-target.angle)/180);
    const angle=target.angle+n*180,offset=n%2?-target.offset:target.offset;
    if(this.cur.width<.3){this.cur.angle=angle;this.cur.offset=offset;}
    else{this.cur.angle=lerp(this.cur.angle,angle,k);this.cur.offset=lerp(this.cur.offset,offset,k);}
    this.cur.width=lerp(this.cur.width,target.width,k);
    this.slitEl.setAttribute('d',slitPath(this.cur.width,this.cur.offset));
    this.slitEl.setAttribute('transform',`rotate(${this.cur.angle}) translate(0 ${this.cur.offset})`);
    this.breathe=lerp(this.breathe,reduced?0:st.breathe,k);
    this.body.setAttribute('transform',`scale(${reduced?1:(1+this.breathe*Math.sin(this.t*1.5))*this.squeeze})`);
  }
}
