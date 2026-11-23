// Run with node test_report.js; no browser or packages required.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const template = fs.readFileSync(`${__dirname}/report_template.html`, 'utf8');
const card = (overrides = {}) => ({textContent: 'Backend Python India', hidden: false, dataset: {
  company: 'Example', source: 'Board', experience: 'possible', mode: 'remote',
  pay: 'unknown', location: 'india', ...overrides,
}});
const cards = Array.from({length: 27}, () => card());
cards[0].textContent = 'Backend engineer distributed systems India';
cards.push(card({experience: 'above_target', company: 'Other', location: 'london', mode: 'hybrid'}));
cards.push(card({experience: 'open', pay: 'compensation_review', source: 'Other board'}));
cards[28].textContent = 'Applied AI agents in India';
cards.push(card({experience: 'unknown', company: ''}));
const elements = {};
const control = () => ({value: '', checked: false, hidden: false, textContent: '', handlers: {}, options: [],
  focus() { this.focused = true; },
  addEventListener(event, handler) { this.handlers[event] = handler; },
  append(...options) { this.options.push(...options); }});
for (const id of ['search','mode','pay','count','page','previous','next','empty','reset']) elements[id] = control();
for (const key of ['company', 'source', 'location']) {
  for (const part of ['search','summary','filter','options','clear','empty']) elements[`${key}-${part}`] = control();
}
const experienceOptions = [...template.matchAll(/<input type="checkbox" name="experience" value="([^"]+)"( checked)?>/g)]
  .map(match => ({...control(), value: match[1], checked: !!match[2], defaultChecked: !!match[2]}));
assert.equal(experienceOptions.length, 4);
const document = {querySelectorAll: selector => selector === 'article' ? cards : experienceOptions,
  getElementById: id => elements[id], createElement: control};
const script = template.match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInNewContext(script, {document});
const visible = () => cards.filter(c => !c.hidden).length;
function set(id, value) {
  elements[id].value = value;
  elements[id].handlers[['search','company-search','source-search','location-search'].includes(id) ? 'input' : 'change']();
}
const options = key => elements[`${key}-options`].options;
const inputs = key => options(key).map(label => label.options[0]);
function selectMulti(key, ...values) {
  inputs(key).forEach(input => { input.checked = values.includes(input.value); });
  inputs(key)[0].handlers.change();
}
function setExperience(...values) {
  experienceOptions.forEach(option => { option.checked = values.includes(option.value); });
  experienceOptions[0].handlers.change();
}
const reset = () => elements.reset.handlers.click();
assert.equal(visible(), 25);
assert.match(elements.count.textContent, /^28 matching roles/);
assert.equal(elements.previous.disabled, true);
elements.next.handlers.click();
assert.equal(visible(), 3);
assert.equal(elements.next.disabled, true);
setExperience('open');
assert.equal(visible(), 1); // Changing categories resets pagination.
set('pay', 'unknown');
assert.equal(visible(), 0);
assert.equal(elements.empty.hidden, false);
assert.equal(elements.next.disabled, true);
reset();
selectMulti('company', 'Other');
assert.equal(visible(), 0); // Above-target roles stay excluded by default.
setExperience('above_target');
assert.equal(visible(), 1);
set('mode', 'remote');
assert.equal(visible(), 0);
set('mode', 'hybrid');
selectMulti('location', 'london');
assert.equal(visible(), 1);
reset();
set('search', 'PYTHON India');
selectMulti('source', 'Other board');
set('pay', 'compensation_review');
assert.equal(visible(), 1);
set('search', 'nonexistent');
assert.equal(visible(), 0);
reset();
setExperience('open', 'unknown');
assert.equal(visible(), 2); // Experience options combine with OR.
setExperience();
assert.equal(visible(), 0);
setExperience('possible', 'open', 'unknown', 'above_target');
assert.match(elements.count.textContent, /^30 matching roles/);
reset();
assert.equal(visible(), 25);
assert.equal(elements.empty.hidden, true);
assert.deepEqual(experienceOptions.filter(o => o.checked).map(o => o.value), ['possible', 'open']);
assert.deepEqual(inputs('company').map(o => o.value), ['', 'Example', 'Other']);
// Search narrows available options without changing selections or job matches.
set('company-search', ' EXAM ');
assert.deepEqual(options('company').filter(o => !o.hidden).map(o => o.options[0].value), ['Example']);
assert.equal(visible(), 25);
selectMulti('company', 'Example');
set('company-search', 'does not exist');
assert.equal(elements['company-empty'].hidden, false);
assert.equal(inputs('company').find(o => o.value === 'Example').checked, true);
assert.equal(elements['company-summary'].textContent, 'Example');
elements['company-clear'].handlers.click();
assert.equal(elements['company-search'].value, '');
assert.equal(elements['company-summary'].textContent, 'All companies');
assert.equal(inputs('company').some(o => o.checked), false);
assert.equal(options('company').every(o => !o.hidden), true);
setExperience('possible', 'open', 'unknown', 'above_target');
selectMulti('company', 'Example', 'Other');
assert.match(elements.count.textContent, /^29 matching roles/);
assert.equal(elements['company-summary'].textContent, '2 companies selected');
selectMulti('source', 'Board', 'Other board');
assert.match(elements.count.textContent, /^29 matching roles/);
assert.equal(elements['source-summary'].textContent, '2 sources selected');
selectMulti('source', 'Other board');
assert.equal(visible(), 1);
selectMulti('company', 'Other');
assert.equal(visible(), 0); // Company and source filters combine with AND.
elements['company-clear'].handlers.click();
assert.equal(visible(), 1);
elements['source-clear'].handlers.click();
assert.match(elements.count.textContent, /^30 matching roles/);
selectMulti('company', ''); // Missing company names remain selectable.
assert.equal(visible(), 1);
assert.equal(elements['company-summary'].textContent, 'Not specified');
set('source-search', 'other');
assert.deepEqual(options('source').filter(o => !o.hidden).map(o => o.options[0].value), ['Other board']);
elements['source-filter'].open = true;
elements['source-filter'].handlers.keydown({key: 'Escape'});
assert.equal(elements['source-filter'].open, false);
assert.equal(elements['source-summary'].focused, true);
reset();
assert.equal(inputs('company').some(o => o.checked), false);
assert.equal(inputs('source').some(o => o.checked), false);
assert.equal(elements['source-search'].value, '');
assert.equal(options('source').every(o => !o.hidden), true);
assert.equal(visible(), 25);
// Location search only narrows available options; chosen labels use exact membership.
assert.deepEqual(inputs('location').map(o => o.value), ['india', 'london']);
set('location-search', ' LON ');
assert.deepEqual(options('location').filter(o => !o.hidden).map(o => o.options[0].value), ['london']);
assert.equal(visible(), 25);
selectMulti('location', 'london');
assert.equal(visible(), 0); // The London fixture is above the default experience target.
setExperience('above_target');
assert.equal(visible(), 1);
selectMulti('location', 'london', 'india');
assert.equal(elements['location-summary'].textContent, '2 locations selected');
setExperience('possible', 'open', 'unknown', 'above_target');
assert.match(elements.count.textContent, /^30 matching roles/);
set('location-search', 'worldwide');
assert.equal(elements['location-empty'].hidden, false); // Remote alone creates no worldwide option.
assert.equal(inputs('location').filter(o => o.checked).length, 2);
reset();
assert.equal(inputs('location').some(o => o.checked), false);
assert.equal(elements['location-search'].value, '');
assert.equal(elements['location-summary'].textContent, 'All locations');
assert.equal(options('location').every(o => !o.hidden), true);
// Main search matches ANY keyword, with comma/space separators and quoted phrases.
set('search', 'unmatchedtoken PYTHON');
assert.match(elements.count.textContent, /^26 matching roles/);
set('search', 'unmatchedtoken, "distributed systems"');
assert.equal(visible(), 1);
set('search', '"distributed nonexistent"');
assert.equal(visible(), 0);
set('search', ' ,  ');
assert.equal(visible(), 25);
set('search', 'agents, nonexistent');
assert.equal(visible(), 1);
selectMulti('location', 'london');
assert.equal(visible(), 0); // OR search still combines with other filters using AND.
elements['location-clear'].handlers.click();
assert.equal(visible(), 1);
reset();
console.log('Searchable multi-selects, combined filters, pagination, empty state and reset passed.');
