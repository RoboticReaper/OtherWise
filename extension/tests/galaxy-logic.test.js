import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareGalaxy, searchTopics, restoreViewState, worldToScreen, screenToWorld, zoomAt, panCamera, hitTest, topicsInDomain} from '../ui/galaxy-logic.js';

const catalog = [
  {id: 'C', topic: 'C', domain: 'Arts', description: 'A description about pottery.'},
  {id: 'A', topic: 'Alpha computing', domain: 'Science', description: 'Original <literal> description.'},
  {id: 'B', topic: 'Beta', domain: 'Science', description: 'Studying computing systems.'},
];
const fixture = () => ({schema_version: 1, cache_key: 'fixture-v1', metadata: {}, domains: [{id: 'Arts', x: -1, y: -1}, {id: 'Science', x: 1, y: 1}], topics: [
  {id: 'A', x: 2, y: 1, neighbors: [{id: 'B', distance: .2}, {id: 'C', distance: .8}]},
  {id: 'B', x: 0, y: 1, neighbors: [{id: 'A', distance: .2}]},
  {id: 'C', x: -2, y: -1, neighbors: [{id: 'A', distance: .8}]},
]});

test('layout joins by stable IDs and retains catalog descriptions and high-dimensional distances', () => {
  const data = prepareGalaxy(catalog, fixture());
  assert.equal(data.byId.get('A').x, 2);
  assert.equal(data.byId.get('C').x, -2);
  assert.equal(data.byId.get('A').description, 'Original <literal> description.');
  assert.deepEqual(data.byId.get('A').neighbors, [{id: 'B', distance: .2}, {id: 'C', distance: .8}]);
  assert.deepEqual(prepareGalaxy([...catalog].reverse(), fixture()).topics.map(t => [t.id,t.x]).sort(), data.topics.map(t => [t.id,t.x]).sort());
});

test('invalid assets fail closed for duplicate IDs, unknown IDs, nonfinite coordinates and distances', () => {
  const cases = [
    x => x.topics.push({...x.topics[0]}), x => x.topics[0].id = 'unknown',
    x => x.topics[0].neighbors[0].id = 'unknown', x => x.topics[0].x = Infinity,
    x => x.topics[0].neighbors[0].distance = -.1, x => x.topics.pop(),
    x => x.domains[0].id = 'Unknown domain', x => x.domains.push({...x.domains[0]}),
    x => x.cache_key = '', x => x.schema_version = 2,
    x => x.topics[0].neighbors.push({id: 'B', distance: .3}),
  ];
  for (const mutate of cases) { const layout = fixture(); mutate(layout); assert.throws(() => prepareGalaxy(catalog, layout)); }
  assert.throws(() => prepareGalaxy([...catalog, {...catalog[0]}], fixture()));
});

test('keyword search prefers literal topic matches, supports descriptions and filters domains', () => {
  const data = prepareGalaxy(catalog, fixture());
  assert.deepEqual(searchTopics(data, 'COMPUTING').map(t => t.id), ['A', 'B']);
  assert.deepEqual(searchTopics(data, 'pottery').map(t => t.id), ['C']);
  assert.deepEqual(searchTopics(data, 'computing', 'Arts'), []);
  assert.deepEqual(searchTopics(data, '   '), []);
  assert.deepEqual(topicsInDomain(data, 'Science').map(t => t.id).sort(), ['A', 'B']);
});

test('view restore clamps invalid values and preserves query filter selection and world camera', () => {
  const data = prepareGalaxy(catalog, fixture());
  const restored = restoreViewState({query: 'compute', domain: 'Science', selected: 'A', camera: {x: 1, y: -.5, zoom: 3}}, data);
  assert.deepEqual(restored, {query: 'compute', domain: 'Science', selected: 'A', camera: {x: 1, y: -.5, zoom: 3}});
  const invalid = restoreViewState({domain: 'missing', selected: 'missing', camera: {x: Infinity, y: 99999, zoom: 99999}}, data);
  assert.equal(invalid.domain, null); assert.equal(invalid.selected, null);
  assert.ok(Number.isFinite(invalid.camera.x)); assert.ok(invalid.camera.y < 100); assert.ok(invalid.camera.zoom <= 20);
});

test('projection resize and pointer-centered zoom preserve world coordinates', () => {
  const bounds = {minX: -2, maxX: 2, minY: -1, maxY: 1};
  const camera = {x: .5, y: -.5, zoom: 2}, viewport = {width: 800, height: 400};
  assert.deepEqual(worldToScreen({x: .5, y: -.5}, camera, viewport, bounds), {x: 400, y: 200});
  assert.deepEqual(worldToScreen({x: .5, y: -.5}, camera, {width: 320, height: 500}, bounds), {x: 160, y: 250});
  const pointer = {x: 630, y: 80}, before = screenToWorld(pointer, camera, viewport, bounds);
  const zoomed = zoomAt(camera, 1.7, pointer, viewport, bounds);
  const after = screenToWorld(pointer, zoomed, viewport, bounds);
  assert.ok(Math.abs(before.x - after.x) < 1e-9); assert.ok(Math.abs(before.y - after.y) < 1e-9);
  const panned = panCamera(camera, 50, -30, viewport, bounds);
  const screen = worldToScreen({x: .5, y: -.5}, panned, viewport, bounds);
  assert.ok(Math.abs(screen.x - 450) < 1e-9); assert.ok(Math.abs(screen.y - 170) < 1e-9);
});

test('hit testing only selects visible domain points within the pointer radius', () => {
  const hits = [{id: 'A', x: 20, y: 10}, {id: 'B', x: 26, y: 10}];
  assert.equal(hitTest(hits, {x: 25, y: 10}, 10), 'B');
  assert.equal(hitTest(hits, {x: 100, y: 100}, 10), null);
  assert.equal(hitTest([], {x: 20, y: 10}), null);
});

test('a wide valid coordinate range still fits within the initial viewport', () => {
  const bounds = {minX: -1000, maxX: 1000, minY: -1000, maxY: 1000};
  const camera = {x: 0, y: 0, zoom: 1}, viewport = {width: 320, height: 390};
  const corner = worldToScreen({x: 1000, y: 1000}, camera, viewport, bounds);
  assert.ok(corner.x < 320 && corner.x > 160);
  assert.ok(corner.y > 0 && corner.y < 195);
});
