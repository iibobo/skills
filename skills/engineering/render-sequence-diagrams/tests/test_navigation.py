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

    @unittest.skipUnless(shutil.which('node'), 'Node is only needed for navigation development tests')
    def test_source_links_use_actor_ids_and_follow_wrapped_messages(self):
        script = r'''
const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');

const links = [];
function text(parts, actorId, participant) {
    return {
        parts,
        textContent: parts.join(''),
        parentElement: {
            getAttribute: name => name === 'name' && !participant ? actorId : null,
            querySelector: () => participant ? {getAttribute: () => actorId} : null,
        },
    };
}
const actors = [
    text(['Worker', 'handler'], 'A', true), text(['Worker', 'handler'], 'B', false),
    text(['Worker', 'handler'], 'A', true), text(['Worker', 'handler'], 'B', false),
];
const messages = [
    text(['start()-']), text(['retry()']), text(['extraordi-']),
    text(['nary work']), text(['finish()']),
];
const mapping = {
    participants: {
        A: {label: 'Worker<br/>handler', links: [{text: 'Worker', symbol: 'A'}]},
        B: {label: 'Worker<br/>handler', links: [{text: 'Worker', symbol: 'B'}]},
    },
    messages: [
        {label: 'start()-<br/>retry()', links: [{text: 'retry', symbol: 'B', method: 'retry'}]},
        {label: 'extraordinary work'},
        {label: 'nowrap: finish()', links: [{text: 'finish', symbol: 'A', method: 'finish'}]},
    ],
};
const symbols = {
    A: {className: 'example.First', methods: {finish: {methodName: 'finish', parameterTypes: []}}},
    B: {className: 'example.Second', methods: {retry: {methodName: 'retry', parameterTypes: []}}},
};
const svg = {
    dataset: {},
    querySelectorAll: selector => selector === 'text.actor' ? actors : messages,
};
const document = {
    getElementById: id => ({textContent: JSON.stringify(id === 'source-map' ? symbols : [mapping])}),
    createElementNS: () => ({dataset: {}, classList: {add() {}}, setAttribute() {}, append() {}, addEventListener() {}}),
    createTextNode: value => value,
    createTreeWalker: element => {
        const nodes = element.parts.map(textContent => ({
            textContent,
            parentElement: {closest: () => null},
            replaceWith: (before, link) => links.push(link.dataset),
        }));
        return {nextNode() { this.currentNode = nodes.shift(); return this.currentNode; }};
    },
};
const context = {document, NodeFilter: {SHOW_TEXT: 4}};
runInNewContext(readFileSync(process.argv[1], 'utf8'), context);
context.linkSequenceSources(svg, 0);

assert.equal(svg.dataset.sourceLinkError, undefined);
assert.deepEqual(links.map(link => [link.sourceSymbol, link.sourceMethod]), [
    ['A', undefined], ['B', undefined], ['A', undefined], ['B', undefined],
    ['B', 'retry'], ['A', 'finish'],
]);
'''
        source = pathlib.Path(__file__).resolve().parents[1] / 'assets/sequence-source-links.js'
        subprocess.run(['node', '-e', script, str(source)], check=True)
