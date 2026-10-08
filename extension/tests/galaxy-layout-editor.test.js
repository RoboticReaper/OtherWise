import test from 'node:test';
import assert from 'node:assert/strict';
import {createGalaxyLayoutEditor} from '../ui/galaxy-layout-editor.js';

// Small DOM surface exercises the editor's asynchronous events without a browser dependency.
class Node {
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.listeners=new Map();this.attributes={};this.classes=new Set();this.classList={add:c=>this.classes.add(c),remove:c=>this.classes.delete(c),toggle:(c,on)=>on?this.classes.add(c):this.classes.delete(c)};}
  set value(v){this.rawValue=String(v);}get value(){return this.rawValue||'';}
  append(...nodes){this.children.push(...nodes);}
  setAttribute(key,value){this.attributes[key]=value;}
  set innerHTML(html){const stack=[this];for(const match of html.matchAll(/<\/?([\w-]+)([^>]*)>/g)){if(match[0].startsWith('</')){stack.pop();continue;}const node=new Node(match[1]);for(const attr of match[2].matchAll(/([\w-]+)="([^"]*)"/g)){if(attr[1]==='class')node.className=attr[2];else if(attr[1].startsWith('data-'))node.dataset[attr[1].slice(5).replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]=attr[2];else node.setAttribute(attr[1],attr[2]);}stack.at(-1).append(node);stack.push(node);}}
  matches(selector){if(selector.startsWith('.'))return this.className?.split(' ').includes(selector.slice(1));const attr=selector.match(/^\[([^=\]]+)(?:="([^"]+)")?\]$/);if(attr){const value=attr[1].startsWith('data-')?this.dataset[attr[1].slice(5).replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]:this[attr[1]];return attr[2]?value===attr[2]:value!==undefined;}return this.tag===selector;}
  querySelectorAll(selector){return this.children.flatMap(child=>[...(child.matches(selector)?[child]:[]),...child.querySelectorAll(selector)]);}
  querySelector(selector){return this.querySelectorAll(selector)[0];}
  addEventListener(type,listener){this.listeners.set(type,listener);}removeEventListener(type){this.listeners.delete(type);}
  closest(selector){return this.matches(selector)?this:null;}remove(){}focus(){}
}

test('Generate and Save recover after successful or failed default persistence; feedback remains visible',async()=>{
  const previous=globalThis.document;globalThis.document={createElement:tag=>new Node(tag)};
  try{
    let settle;const editor=createGalaxyLayoutEditor({host:new Node('host'),text:key=>key,getOptions:()=>undefined,onGenerate:async()=>{},onReset:()=>{},onSave:()=>new Promise((resolve,reject)=>settle={resolve,reject})});
    const panel=editor.element,generate=panel.querySelector('[data-layout-action="generate"]'),save=panel.querySelector('[data-layout-action="save"]'),status=panel.querySelector('.galaxy-layout-status');
    const click=()=>panel.listeners.get('click')({target:save});
    const success=click();assert.equal(generate.disabled,true);assert.equal(save.disabled,true);assert.equal(panel.attributes['aria-busy'],'true');settle.resolve();await success;
    assert.equal(generate.disabled,false);assert.equal(save.disabled,false);assert.equal(panel.attributes['aria-busy'],'false');assert.equal(status.textContent,'layoutSaved');
    const failed=click();settle.reject(new Error('Persistence failed'));await failed;
    assert.equal(generate.disabled,false);assert.equal(save.disabled,false);assert.equal(panel.attributes['aria-busy'],'false');assert.equal(status.textContent,'Persistence failed');assert.equal(status.classes.has('is-error'),true);editor.destroy();
  }finally{globalThis.document=previous;}
});
