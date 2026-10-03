import test from 'node:test';
import assert from 'node:assert/strict';
import {createState, reduceState, prepareObservation, hashUrl, buildRequest, isAllowedUrl} from '../core/index.js';

const NOW = 1_800_000_000_000;
const DAY = 86_400_000;
const catalog = [
  {id:'Basketball',topic:'Basketball',domain:'Sports',description:'Team sport'},
  {id:'Python programming',topic:'Python programming',domain:'Computing',description:'Programming language'},
  {id:'Machine learning',topic:'Machine learning',domain:'Computing',description:'Statistical learning'},
  {id:'Art',topic:'Art',domain:'Arts',description:'Visual expression'},
];
const topic = name => ({id:name,topic:name,domain:'Custom',description:''});
const observe = (name, hash='hash-'+name, at=NOW) => ({sourceHash:hash,host:'example.org',seenAt:at,topicIds:[name],topics:[topic(name)],source:'Chrome'});
const apply = (state,type,fields={},at=NOW) => reduceState(state,{type,...fields},at);
const approved = (...names) => names.reduce((s,name)=>apply(s,'ADD_INTEREST',{topic:name}),createState(NOW));

test('recommendation options migrate safely and only finite bounded numbers enter the request',()=>{
  let state=approved('Basketball'); delete state.settings.recommendationOptions;
  state=apply(state,'PRUNE');
  assert.deepEqual(state.settings.recommendationOptions,{limit:10,radius:.28,expansion:.07,overlap:.015,diversity:.2,max_overlap_fraction:.2,randomness:.03});
  state=apply(state,'SET_SETTINGS',{patch:{recommendationOptions:{limit:75,overlap:.025,diversity:.4}}});
  assert.equal(buildRequest(state).limit,75); assert.equal(buildRequest(state).overlap,.025);
  assert.equal(buildRequest(state).radius,.28);
  const before=state;
  for(const options of [{limit:101},{limit:2.5},{radius:NaN},{expansion:Infinity},{overlap:-.1},{diversity:'0.2'},{randomness:true},{max_overlap_fraction:1},{private_topic:'secret'},null,[]]){
    state=apply(before,'SET_SETTINGS',{patch:{recommendationOptions:options}});
    assert.deepEqual(state.settings.recommendationOptions,before.settings.recommendationOptions);
    assert.equal(state.generation,before.generation);
    assert.match(state.lastError,/recommendation settings/i);
  }
  state.settings.recommendationOptions={limit:1000,radius:NaN,overlap:.02,private_topic:'secret'};
  const request=buildRequest(state);
  assert.equal(request.limit,10); assert.equal(request.radius,.28); assert.equal(request.overlap,.02);
  assert.equal('private_topic' in request,false);
});

test('large batches remain available locally after dismissing without changing interests or request',()=>{
  let state=approved('Basketball');
  state=apply(state,'SET_SETTINGS',{patch:{recommendationOptions:{limit:100}}});
  const request=buildRequest(state);
  state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:Array.from({length:100},(_,i)=>topic(`Topic ${i}`))});
  assert.equal(state.recommendations.length,100);
  state=apply(state,'DISMISS',{id:'Topic 0'});
  assert.equal(state.recommendations.length,99); assert.deepEqual(buildRequest(state),request);
  state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:[topic('Topic 0'),topic('Fresh')]});
  assert.deepEqual(state.recommendations.map(x=>x.topic),['Fresh']);
});

test('defaults disable analysis and refresh; every install uses a new salt',()=>{
  const a=createState(NOW), b=createState(NOW);
  assert.equal(a.settings.browsingEnabled,false); assert.equal(a.settings.autoRefresh,false);
  assert.equal(a.settings.mode,'path'); assert.equal(a.settings.globalLevel,0);
  assert.equal(a.schemaVersion,1); assert.equal(a.generation,0);
  assert.ok(a.salt.length>=32); assert.notEqual(a.salt,b.salt);
  assert.deepEqual(a.approved,[]); assert.equal(a.focus,null);
});

test('URL filter blocks local addresses, nonweb schemes, credentials and sensitive domains',()=>{
  const blocked=['mail.google.com','docs.google.com'];
  for(const url of ['file:///etc/passwd','chrome://history','https://localhost/a','http://127.0.0.1','http://10.1.2.3','http://172.16.0.3','http://192.168.1.1','http://169.254.1.1','https://[::1]/','https://[fc00::1]/','https://[fe80::1]/','https://[::ffff:127.0.0.1]/','https://foo.local','https://mail.google.com','https://a.docs.google.com','https://user:pass@example.org']) assert.equal(isAllowedUrl(url,blocked),false,url);
  for(const url of ['https://youtube.com/watch?v=1','https://example.org','http://172.32.0.1','https://notdocs.google.com']) assert.equal(isAllowedUrl(url,blocked),true,url);
});

test('default sensitive-domain list filters common account, mail, banking and document services',()=>{
  const state=createState(NOW);
  for(const host of ['mail.google.com','docs.google.com','accounts.google.com','outlook.live.com','chase.com']) assert.equal(isAllowedUrl('https://'+host,state.settings.blockedDomains),false,host);
});

test('hashes are deterministic per salt and never preserve the URL',async()=>{
  const a=await hashUrl('https://example.org/private?q=secret','one');
  assert.equal(a,await hashUrl('https://example.org/private?q=secret','one'));
  assert.notEqual(a,await hashUrl('https://example.org/private?q=secret','two'));
  assert.match(a,/^[a-f0-9]{64}$/);
});

test('title matching uses catalog phrases and practical aliases, without guessing from URL',async()=>{
  const options={salt:'test-salt',blockedDomains:[]};
  const result=await prepareObservation({url:'https://www.youtube.com/watch?v=private',title:'NBA highlights | Python tutorial and machine learning',lastVisitTime:NOW},catalog,options,NOW);
  assert.deepEqual(result.topicIds,['Basketball','Python programming','Machine learning']);
  assert.equal(result.source,'YouTube'); assert.equal(result.host,'www.youtube.com');
  assert.equal(result.seenAt,NOW); assert.equal(result.topics[0].domain,'Sports');
  assert.equal(JSON.stringify(result).includes('NBA'),false);
  assert.equal(JSON.stringify(result).includes('private'),false);
  assert.equal(await prepareObservation({url:'https://example.org/Python',title:''},catalog,options,NOW),null);
  assert.equal(await prepareObservation({url:'https://example.org',title:'A personal private novel title'},catalog,options,NOW),null);
  assert.equal(await prepareObservation({url:'https://example.org',title:'Party starts now'},catalog,options,NOW),null);
  assert.equal(await prepareObservation({url:'https://example.org',title:'the and for'},[{id:'The',topic:'The',domain:'X',description:''}],options,NOW),null);
});

test('observations reject blocked URLs and old evidence before extraction',async()=>{
  const options={salt:'x',blockedDomains:['docs.google.com']};
  assert.equal(await prepareObservation({url:'https://docs.google.com/a',title:'Basketball'},catalog,options,NOW),null);
  assert.equal(await prepareObservation({url:'https://example.org',title:'Basketball',lastVisitTime:NOW-31*DAY},catalog,options,NOW),null);
});

test('ingest creates review candidates and keeps minimal unique evidence, never approved interests',()=>{
  const original=createState(NOW); const obs={...observe('Basketball'),url:'https://private',title:'secret title'};
  const next=apply(original,'INGEST',{observations:[obs,obs]});
  assert.deepEqual(original.candidates,[]); assert.equal(next.candidates.length,1); assert.equal(next.candidates[0].count,1);
  assert.deepEqual(next.candidates[0].sources,['Chrome']); assert.deepEqual(next.approved,[]);
  assert.equal(next.evidence.length,1); assert.deepEqual(Object.keys(next.evidence[0]).sort(),['host','seenAt','source','sourceHash','topicIds']);
  assert.equal(JSON.stringify(next).includes('secret title'),false); assert.equal(JSON.stringify(next).includes('https://private'),false);
  assert.throws(()=>buildRequest(next),/interest/i);
});

test('approve selected candidates makes an initial baseline and sends only fixed approved request fields',()=>{
  let state=apply(createState(NOW),'INGEST',{observations:[observe('Basketball'),observe('Machine learning')]});
  state=apply(state,'APPROVE',{ids:['Basketball']});
  assert.deepEqual(state.approved.map(x=>x.id),['Basketball']); assert.deepEqual(state.baseline,['Basketball']);
  assert.equal(state.focus,'Basketball'); assert.equal(state.settings.globalLevel,0);
  assert.deepEqual(buildRequest(state),{keywords:['Basketball'],mode:'path',focus:'Basketball',expansion_level:0,limit:10,radius:.28,expansion:.07,overlap:.015,diversity:.2,max_overlap_fraction:.2,randomness:.03});
  assert.deepEqual(state.candidates.map(x=>x.id),['Machine learning']);
});

test('unique explicit approval advances only global mode, capped at eight; search and duplicate approval do not',()=>{
  let state=approved('Initial'); state=apply(state,'ADD_INTEREST',{topic:'Path addition'});
  assert.equal(state.settings.globalLevel,0);
  state=apply(state,'SET_SETTINGS',{patch:{mode:'global'}});
  for(let i=0;i<12;i++) state=apply(state,'ADD_INTEREST',{topic:'New topic '+i});
  assert.equal(state.settings.globalLevel,8);
  const generation=state.generation;
  state=apply(state,'ADD_INTEREST',{topic:'New topic 11'}); state=apply(state,'EXPLORE',{topic:topic('Search result'),parentId:'Initial'});
  assert.equal(state.settings.globalLevel,8); assert.equal(state.generation,generation); assert.equal(state.approved.length,14);
  assert.equal(state.explored.length,1); assert.equal(state.edges[0].from,'Initial');
});

test('settings cannot silently widen global expansion and request clamps tampered state to contract',()=>{
  let state=approved('Basketball'); state=apply(state,'SET_SETTINGS',{patch:{globalLevel:99,mode:'global'}});
  assert.equal(state.settings.globalLevel,0);
  const request=buildRequest({...state,focus:'Unknown',settings:{...state.settings,globalLevel:99}});
  assert.equal(request.expansion_level,8); assert.equal(request.focus,null); assert.equal(request.mode,'global');
  assert.equal('salt' in request,false); assert.equal('evidence' in request,false);
});

test('manual topics reject URLs emails multiline and long text with safe errors; records preserve catalog metadata',()=>{
  for(const value of ['https://example.org','me@example.org','a\nb','x'.repeat(81),'','example.com']) {
    const state=apply(createState(NOW),'ADD_INTEREST',{topic:value});
    assert.equal(state.approved.length,0,value); assert.match(state.lastError,/topic|interest/i); assert.equal(state.lastError.includes(value)&&value.length>0,false);
  }
  const state=apply(createState(NOW),'ADD_INTEREST',{topic:catalog[0]});
  assert.equal(state.approved[0].domain,'Sports'); assert.equal(state.approved[0].addedAt,NOW);
});

test('interest limit is enforced before sending and no malformed keywords can enter wire object',()=>{
  let state=createState(NOW);
  for(let i=0;i<41;i++) state=apply(state,'ADD_INTEREST',{topic:'Topic '+i});
  assert.equal(state.approved.length,40); assert.match(state.lastError,/40/);
  assert.throws(()=>buildRequest({...state,approved:[topic('https://secret.example')]}),/topic|interest/i);
});

test('dismissed or removed interests stay suppressed across future history observations',()=>{
  let state=apply(createState(NOW),'INGEST',{observations:[observe('Basketball')]});
  state=apply(state,'DISMISS',{id:'Basketball'}); state=apply(state,'INGEST',{observations:[observe('Basketball','new-hash')]});
  assert.deepEqual(state.candidates,[]); assert.deepEqual(state.suppressed,['Basketball']);
  state=apply(state,'ADD_INTEREST',{topic:catalog[0]}); assert.deepEqual(state.suppressed,[]);
  state=apply(state,'REMOVE_INTEREST',{id:'Basketball'}); assert.deepEqual(state.approved,[]); assert.deepEqual(state.baseline,[]); assert.equal(state.focus,null);
  state=apply(state,'INGEST',{observations:[observe('Basketball','third')]}); assert.deepEqual(state.candidates,[]);
});

test('evidence deletion recomputes candidates and expiry does not delete explicitly approved or explored topics',()=>{
  let state=apply(createState(NOW),'INGEST',{observations:[observe('Basketball','one'),observe('Basketball','two'),observe('Python programming','three')]});
  state=apply(state,'DELETE_SOURCES',{hashes:['one']}); assert.equal(state.candidates.find(x=>x.id==='Basketball').count,1);
  state=apply(state,'DELETE_SOURCES',{hashes:['two']}); assert.deepEqual(state.candidates.map(x=>x.id),['Python programming']);
  state=apply(state,'ADD_INTEREST',{topic:catalog[0]}); state=apply(state,'EXPLORE',{topic:catalog[1],parentId:'Basketball'});
  state=apply(state,'CLEAR_ERROR',{},NOW+31*DAY);
  assert.deepEqual(state.evidence,[]); assert.deepEqual(state.candidates,[]); assert.equal(state.approved.length,1); assert.equal(state.explored.length,1);
});

test('privacy/settings/profile changes invalidate stale recommendations and focus remains approved',()=>{
  let state=approved('Basketball','Python programming'); const old=state.generation;
  state=apply(state,'SET_SETTINGS',{patch:{browsingEnabled:true}}); assert.equal(state.settings.analysisSince,NOW); assert.ok(state.generation>old);
  state=apply(state,'RECOMMENDATIONS',{generation:old,items:[topic('Stale')]}); assert.deepEqual(state.recommendations,[]);
  state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:[topic('Current')]}); assert.equal(state.recommendations.length,1);
  state=apply(state,'REMOVE_INTEREST',{id:'Python programming'}); assert.equal(state.focus,'Basketball'); assert.deepEqual(state.recommendations,[]);
  const generation=state.generation;
  state=apply(state,'SET_SETTINGS',{patch:{browsingEnabled:false}},NOW+DAY); assert.ok(state.generation>generation);
  state=apply(state,'SET_SETTINGS',{patch:{browsingEnabled:true}},NOW+2*DAY); assert.equal(state.settings.analysisSince,NOW+2*DAY);
});

test('ingest optional generation guard ignores old queued observations',()=>{
  let state=createState(NOW); state=apply(state,'CLEAR_DERIVED');
  state=apply(state,'INGEST',{generation:0,observations:[observe('Basketball')]}); assert.deepEqual(state.evidence,[]);
});

test('clear-derived and full history deletion preserve explicit choices and paths while reset removes all data and token',()=>{
  let state=approved('Basketball'); state=apply(state,'EXPLORE',{topic:catalog[1],parentId:'Basketball'});
  state=apply(state,'INGEST',{observations:[observe('Machine learning')]}); state=apply(state,'SET_SETTINGS',{patch:{accessToken:'private-token',autoRefresh:true}});
  for(const action of [{type:'CLEAR_DERIVED'},{type:'DELETE_SOURCES',all:true}]) {
    const next=reduceState(state,action,NOW); assert.deepEqual(next.evidence,[]); assert.deepEqual(next.candidates,[]);
    assert.equal(next.approved.length,1); assert.equal(next.explored.length,1); assert.ok(next.generation>state.generation);
  }
  const next=apply(state,'RESET'); assert.deepEqual(next.approved,[]); assert.deepEqual(next.explored,[]); assert.deepEqual(next.baseline,[]);
  assert.equal(next.settings.accessToken,''); assert.equal(next.settings.autoRefresh,false); assert.notEqual(next.salt,state.salt); assert.ok(next.generation>state.generation);
  assert.equal(apply(next,'RECOMMENDATIONS',{generation:state.generation,items:[topic('Stale')]}).recommendations.length,0);
});

test('reducers never mutate frozen input or retain action object references',()=>{
  const original=createState(NOW); Object.freeze(original.settings); Object.freeze(original.candidates); Object.freeze(original.evidence); Object.freeze(original);
  const observation=observe('Basketball'); const next=apply(original,'INGEST',{observations:[observation]});
  observation.topicIds.push('Private title'); observation.topics[0].topic='Private title';
  assert.deepEqual(next.evidence[0].topicIds,['Basketball']); assert.equal(next.candidates[0].topic,'Basketball'); assert.deepEqual(original.candidates,[]);
});

test('a malformed observation cannot persist raw URL fragments in a hostname or fake a future timestamp',()=>{
  const state=apply(createState(NOW),'INGEST',{observations:[
    {...observe('Basketball'),host:'example.org/private?secret=1'},
    {...observe('Python programming','future',NOW+DAY)},
  ]});
  assert.deepEqual(state.evidence,[]); assert.deepEqual(state.candidates,[]);
});

test('manual topics reject executable URL schemes and non-topic punctuation',()=>{
  for(const value of ['javascript:alert(1)','data:text/plain,secret','about:blank','chrome:history','!!!']) {
    const state=apply(createState(NOW),'ADD_INTEREST',{topic:value});
    assert.deepEqual(state.approved,[],value); assert.ok(state.lastError);
  }
});

test('removed baseline remains removed and onboarding cannot restart to bypass global expansion',()=>{
  let state=approved('Basketball'); state=apply(state,'REMOVE_INTEREST',{id:'Basketball'});
  state=apply(state,'SET_SETTINGS',{patch:{mode:'global'}}); state=apply(state,'ADD_INTEREST',{topic:'Gardening'});
  assert.deepEqual(state.baseline,[]); assert.equal(state.settings.globalLevel,1); assert.equal(state.focus,'Gardening');
});

test('candidate metadata survives partial evidence deletion after reloading serialized state',()=>{
  let state=apply(createState(NOW),'INGEST',{observations:[
    {...observe('Basketball','first'),topics:[catalog[0]]},
    {...observe('Basketball','second'),topics:[catalog[0]],source:'YouTube'},
  ]});
  state=JSON.parse(JSON.stringify(state)); state=apply(state,'DELETE_SOURCES',{hashes:['first']});
  assert.equal(state.candidates[0].domain,'Sports'); assert.equal(state.candidates[0].count,1); assert.deepEqual(state.candidates[0].sources,['YouTube']);
});

test('stale errors and generationless recommendation responses cannot restore reset state',()=>{
  const state=apply(approved('Basketball'),'RESET');
  assert.equal(apply(state,'ERROR',{generation:0,message:'old private problem'}).lastError,null);
  assert.deepEqual(apply(state,'RECOMMENDATIONS',{items:[catalog[0]]}).recommendations,[]);
});

test('multi-topic onboarding in global mode never expands until a later explicit approval',()=>{
  let state=apply(createState(NOW),'SET_SETTINGS',{patch:{mode:'global'}});
  state=apply(state,'INGEST',{observations:[observe('Basketball'),observe('Python programming')]});
  state=apply(state,'APPROVE',{ids:['Basketball','Python programming']}); assert.equal(state.settings.globalLevel,0);
  assert.deepEqual([...state.baseline].sort(),['Basketball','Python programming']);
  state=apply(state,'APPROVE',{ids:['Basketball','Python programming']}); assert.equal(state.settings.globalLevel,0);
  state=apply(state,'ADD_INTEREST',{topic:'Gardening'}); assert.equal(state.settings.globalLevel,1);
});

test('invalid connection address reports a recoverable error even when another setting changes',()=>{
  const state=apply(createState(NOW),'SET_SETTINGS',{patch:{endpoint:'https://secret.example/?token=secret',autoRefresh:true}});
  assert.equal(state.settings.autoRefresh,true); assert.equal(state.settings.endpoint,'http://127.0.0.1:8000');
  assert.match(state.lastError,/service address/i); assert.equal(state.lastError.includes('secret'),false);
});

test('focus changes use only approved interests and invalidate recommendations without advancing expansion',()=>{
  let state=approved('Basketball','Python programming');
  state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:[topic('Gardening')]});
  const generation=state.generation;
  state=apply(state,'SET_FOCUS',{id:'Basketball'});
  assert.equal(state.focus,'Basketball'); assert.ok(state.generation>generation);
  assert.equal(state.settings.globalLevel,0); assert.equal(state.approved.length,2); assert.deepEqual(state.recommendations,[]);
  const savedGeneration=state.generation;
  state=apply(state,'SET_FOCUS',{id:'Unconfirmed'}); assert.equal(state.focus,'Basketball'); assert.equal(state.generation,savedGeneration);
  state=apply(state,'SET_FOCUS',{id:'Basketball'}); assert.equal(state.generation,savedGeneration);
});

test('correcting a rejected manual topic clears the previous validation error',()=>{
  let state=apply(createState(NOW),'ADD_INTEREST',{topic:'https://private.example'});
  assert.ok(state.lastError);
  state=apply(state,'ADD_INTEREST',{topic:'Basketball'});
  assert.equal(state.approved.length,1); assert.equal(state.lastError,null);
});

test('dismiss removes a visible recommendation and suppresses it from future refreshes until explicit approval',()=>{
  let state=approved('Basketball'); state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:[catalog[1],catalog[2]]});
  state=apply(state,'DISMISS',{id:'Python programming'}); assert.deepEqual(state.recommendations.map(x=>x.id),['Machine learning']);
  state=apply(state,'RECOMMENDATIONS',{generation:state.generation,items:[catalog[1],catalog[2]]});
  assert.deepEqual(state.recommendations.map(x=>x.id),['Machine learning']);
  state=apply(state,'ADD_INTEREST',{topic:catalog[1]}); assert.equal(state.suppressed.includes('Python programming'),false);
  assert.equal(state.approved.some(x=>x.id==='Python programming'),true);
});

test('repeated extraction from an immutable catalog keeps alias matching and independent result metadata',async()=>{
  const immutableCatalog=Object.freeze(catalog.map(item=>Object.freeze({...item})));
  const options={salt:'fixed-salt',blockedDomains:[]};
  const first=await prepareObservation({url:'https://example.org/a',title:'NBA Python tutorial',lastVisitTime:NOW},immutableCatalog,options,NOW);
  first.topics[0].topic='Changed outside'; first.topics[0].domain='Changed outside';
  const second=await prepareObservation({url:'https://example.org/b',title:'Python and NBA',lastVisitTime:NOW},immutableCatalog,options,NOW);
  assert.deepEqual(second.topicIds,['Basketball','Python programming']); assert.equal(second.topics[0].topic,'Basketball'); assert.equal(second.topics[0].domain,'Sports');
});
