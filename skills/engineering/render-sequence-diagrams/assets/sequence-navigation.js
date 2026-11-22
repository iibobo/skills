// Touch and trackpad scrolling stay native. Mouse dragging adds frame-based momentum.
function installSequenceSwipe(navigation) {
  const tabs=navigation.querySelector('#tabs');
  const reducedMotion=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let pointer=null,frame=0,suppressClickUntil=0;
  const stop=()=>{if(frame)cancelAnimationFrame(frame);frame=0;};
  function coast(velocity){
    if(reducedMotion()||Math.abs(velocity)<0.04)return;
    let previous=performance.now();
    const tick=now=>{
      const dt=Math.min(32,now-previous);previous=now;
      const before=tabs.scrollLeft;
      tabs.scrollLeft+=velocity*dt;
      velocity*=Math.exp(-dt/180);
      if(Math.abs(velocity)>0.04 && Math.abs(tabs.scrollLeft-before)>0.01)frame=requestAnimationFrame(tick);
      else frame=0;
    };
    frame=requestAnimationFrame(tick);
  }
  tabs.addEventListener('pointerdown',event=>{
    stop();
    if(!event.isPrimary||event.pointerType!=='mouse'||event.button!==0){pointer=null;return;}
    pointer={id:event.pointerId,x:event.clientX,y:event.clientY,lastX:event.clientX,lastTime:performance.now(),velocity:0,dragging:false};
  });
  tabs.addEventListener('pointermove',event=>{
    if(!pointer||pointer.id!==event.pointerId)return;
    const dx=event.clientX-pointer.x,dy=event.clientY-pointer.y;
    if(!pointer.dragging && Math.abs(dx)>5 && Math.abs(dx)>Math.abs(dy)){
      pointer.dragging=true;tabs.setPointerCapture(event.pointerId);tabs.classList.add('is-dragging');
    }
    if(!pointer.dragging)return;
    const now=performance.now(),dt=Math.max(1,now-pointer.lastTime);
    const before=tabs.scrollLeft;tabs.scrollLeft+=pointer.lastX-event.clientX;
    const sample=(tabs.scrollLeft-before)/dt;
    pointer.velocity=pointer.velocity*0.35+sample*0.65;
    pointer.lastX=event.clientX;pointer.lastTime=now;
    suppressClickUntil=Date.now()+350;event.preventDefault();
  });
  function finish(event,cancelled){
    if(!pointer||pointer.id!==event.pointerId)return;
    const p=pointer;pointer=null;tabs.classList.remove('is-dragging');
    if(tabs.hasPointerCapture(event.pointerId))tabs.releasePointerCapture(event.pointerId);
    if(p.dragging){suppressClickUntil=Date.now()+350;if(!cancelled&&performance.now()-p.lastTime<80)coast(p.velocity);}
  }
  tabs.addEventListener('pointerup',event=>finish(event,false));
  tabs.addEventListener('pointercancel',event=>finish(event,true));
  tabs.addEventListener('lostpointercapture',event=>finish(event,true));
  tabs.addEventListener('dragstart',event=>event.preventDefault());
  tabs.addEventListener('click',event=>{
    if(event.detail!==0 && Date.now()<suppressClickUntil){event.preventDefault();event.stopImmediatePropagation();}
  },true);
  tabs.addEventListener('wheel',event=>{
    stop();
    if(event.ctrlKey||event.metaKey||event.deltaX||event.shiftKey||!event.deltaY)return;
    const unit=event.deltaMode===1?16:event.deltaMode===2?tabs.clientWidth:1;
    const delta=event.deltaY*unit,max=tabs.scrollWidth-tabs.clientWidth;
    if((delta<0&&tabs.scrollLeft>0)||(delta>0&&tabs.scrollLeft<max)){
      event.preventDefault();tabs.scrollLeft+=delta;
    }
  },{passive:false});
  // Selecting a scene or using the keyboard interrupts an old fling.
  tabs.addEventListener('keydown',stop);
  navigation.querySelectorAll('.nav-arrow').forEach(button=>button.addEventListener('pointerdown',stop));
  document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();pointer=null;tabs.classList.remove('is-dragging');}});
}
