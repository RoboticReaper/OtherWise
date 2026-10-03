import test from 'node:test';import assert from 'node:assert/strict';
import {focusRequestKey,focusFailure} from '../ui/map-workspace-model.js';
const identity={catalog_sha256:'a'.repeat(64),model:'mpnet',embedding:{sha256:'b'.repeat(64),dtype:'float32',shape:[100,768]}};
test('request keys normalize endpoint, exclude credentials and isolate authorization/options/source/seed',()=>{
 const input={endpoint:'https://example.org/',epoch:1,identity,seedId:'A',options:{},accessToken:'never-in-key'};
 const key=focusRequestKey(input);assert.equal(key,focusRequestKey({...input,endpoint:'https://example.org'}));assert.ok(!key.includes('never-in-key'));
 for(const change of [{epoch:2},{seedId:'B'},{options:{limit:20}},{identity:{...identity,model:'other'}}])assert.notEqual(key,focusRequestKey({...input,...change}));
});
test('only controlled messages map to actionable guidance; unknown text never passes through',()=>{
 assert.equal(focusFailure('Add your connection and team access code in Settings.'),'unconfigured');
 assert.equal(focusFailure('The Focus request took too long. Try again.'),'timeout');
 assert.equal(focusFailure('The service and Galaxy data do not match. Update the data before trying again.'),'version');
 assert.equal(focusFailure('Save the connection in Settings to allow this service.'),'permission');
 assert.equal(focusFailure('private server text'),'unavailable');
});
