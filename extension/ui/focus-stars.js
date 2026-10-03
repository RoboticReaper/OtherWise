// Adapted from BowenX307/otherwise@8281161 src/universe/starfield.ts.
// No simulation/engine dependency, mutable personal state or private animation loop.
const TILE=2600,mod=(a,n)=>((a%n)+n)%n;
export function createStarLayers(compact=false){
  let value=42;
  const random=()=>{value=(Math.imul(value,1664525)+1013904223)>>>0;return value/4294967296;};
  const make=(count,rMin,rMax,aMax)=>Array.from({length:count},()=>({x:random()*TILE,y:random()*TILE,r:rMin+random()*(rMax-rMin),a:.12+random()*(aMax-.12),speed:.4+random()*1.6,phase:random()*Math.PI*2}));
  return [{depth:.15,stars:make(compact?100:480,.3,.6,.35)},
    {depth:.4,stars:make(compact?45:170,.45,.85,.5)},
    {depth:.75,stars:make(compact?10:45,.7,1.2,.7)}];
}
export function drawBackground(ctx,view,{time=0,motion=true},layers,wave=null){
  const {width:W,height:H,scale:S,camX=0,camY=0,parX=0,parY=0,cx=W/2,cy=H/2}=view;
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#080d16';ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#f3f1ea';
  const cos=Math.cos(Math.PI/18),sin=Math.sin(Math.PI/18);
  for(const layer of layers){
    const ox=-camX*S*layer.depth-(motion?parX:0)*22*layer.depth;
    const oy=camY*S*layer.depth-(motion?parY:0)*22*layer.depth;
    for(const star of layer.stars){
      const x=mod(star.x+ox,TILE)-(TILE-W)/2,y=mod(star.y+oy,TILE)-(TILE-H)/2;
      if(x<-2||y<-2||x>W+2||y>H+2)continue;
      const twinkle=motion?.55+.45*Math.sin(time*star.speed+star.phase):.8;
      let boost=0;
      if(motion&&wave&&wave.rx>0&&wave.ry>0){
        const dx=x-cx,dy=y-cy,e=Math.hypot((dx*cos-dy*sin)/wave.rx,(dx*sin+dy*cos)/wave.ry);
        boost=wave.strength*Math.exp(-(((e-1)/.07)**2));
      }
      ctx.globalAlpha=Math.min(1,star.a*twinkle+boost);ctx.beginPath();
      ctx.arc(x,y,star.r*(1+boost*1.4),0,Math.PI*2);ctx.fill();
    }
  }
  ctx.globalAlpha=1;
}
