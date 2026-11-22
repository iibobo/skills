import pathlib
import shutil
import subprocess
import unittest

class NavigationGestureTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is only needed for gesture development tests')
    def test_continuous_drag_momentum_native_scroll_and_cancellation(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
let now=1000,frame,position=100,reduced=false;const handlers={};
const tabs={clientWidth:300,scrollWidth:1500,get scrollLeft(){return position},set scrollLeft(n){position=Math.max(0,Math.min(1200,n))},addEventListener:(t,fn)=>handlers[t]=fn,setPointerCapture(){},hasPointerCapture:()=>false,classList:{add(){},remove(){}}};
const nav={querySelector:()=>tabs,querySelectorAll:()=>[]};
const ctx={Date:{now:()=>now},performance:{now:()=>now},requestAnimationFrame:fn=>(frame=fn,1),cancelAnimationFrame:()=>frame=null,window:{matchMedia:()=>({matches:reduced})},document:{addEventListener(){}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),ctx);ctx.installSequenceSwipe(nav);
const fire=(type,props={})=>{now+=16;const e={isPrimary:true,pointerType:'mouse',button:0,pointerId:1,clientX:300,clientY:20,deltaX:0,deltaY:0,deltaMode:0,preventDefault(){this.prevented=true},stopImmediatePropagation(){this.stopped=true},...props};handlers[type](e);return e};
fire('pointerdown');fire('pointermove',{clientX:260});assert.equal(position,140);fire('pointermove',{clientX:220});assert.equal(position,180);fire('pointerup',{clientX:220});assert.equal(fire('click').stopped,true);assert.equal(fire('click',{detail:0}).stopped,undefined);assert.ok(frame);const f=frame;frame=null;now+=16;f(now);assert.ok(position>180);
fire('pointerdown');assert.equal(frame,null);now+=400;assert.equal(fire('click').stopped,undefined);
const before=position;fire('pointermove',{clientX:400});assert.ok(position<before);fire('pointercancel');assert.equal(frame,null);
fire('pointerdown',{pointerType:'touch'});const native=position;fire('pointermove',{pointerType:'touch',clientX:100});assert.equal(position,native);
assert.equal(fire('wheel',{deltaX:80}).prevented,undefined);assert.equal(position,native);
fire('wheel',{deltaY:60});assert.equal(position,native+60);position=1200;assert.equal(fire('wheel',{deltaY:100}).prevented,undefined);
reduced=true;position=300;fire('pointerdown');fire('pointermove',{clientX:200});fire('pointerup');assert.equal(frame,null);
'''
        source = pathlib.Path(__file__).resolve().parents[1] / 'assets/sequence-navigation.js'
        subprocess.run(['node', '-e', script, str(source)], check=True)
