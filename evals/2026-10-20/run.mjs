// Optional maintainer fixture. Uses an existing Playwright installation; installs nothing.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const phase=process.argv[2]??'check';
assert(['reference','check'].includes(phase));
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const files=phase==='reference'?['reference.html','start.html']:['reference.html','start.html','app.html'];
const contents=Object.fromEntries(await Promise.all(files.map(async name=>[name,await readFile(path.join(root,name))])));
const digest=data=>createHash('sha256').update(data).digest('hex');
const before=Object.fromEntries(files.map(name=>[name,digest(contents[name])]));
const server=http.createServer((req,res)=>{
  const name=(req.url??'').slice(1);
  if(!Object.hasOwn(contents,name)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type','text/html; charset=utf-8');res.end(contents[name]);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
let browser;
try{
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:960,height:640},deviceScaleFactor:1,locale:'en-US',colorScheme:'light'});
  const page=await context.newPage();
  const out=path.join(root,'captures');await mkdir(out,{recursive:true});
  const capture=async(name,shot)=>{
    await page.goto(`${origin}/${name}`);await page.evaluate(()=>document.fonts.ready);
    await page.screenshot({path:path.join(out,shot)});
    return await page.locator('nav').boundingBox();
  };
  const reference=await capture('reference.html','reference.png');
  const starting=await capture('start.html','start.png');
  assert(reference.width<reference.height && starting.width>starting.height,'Fixture must expose rail vs tabs');
  const results={date:new Date().toISOString(),phase,browser:browser.version(),node:process.version,
    viewport:{width:960,height:640},dpr:1,startingHashes:before,geometry:{reference,starting},
    limits:['Same-author synthetic fixture, not independent skill efficacy','Image inspection must be recorded separately','No native device, PDF or cross-host activation trial']};
  if(phase==='check'){
    const final=await capture('app.html','final.png');
    assert.deepEqual(final,reference,'Final navigation bounds must match reference');
    results.geometry.final=final;
    await page.getByLabel('Display name').fill('Reopened Name');
    await page.getByRole('button',{name:'Save changes'}).click();
    assert.equal(await page.locator('output').textContent(),'Saved');
    await page.reload();
    assert.equal(await page.getByLabel('Display name').inputValue(),'Reopened Name');
    assert.equal(await page.evaluate(()=>localStorage.getItem('display-name')),'Reopened Name');
    await page.screenshot({path:path.join(out,'saved-after-reload.png')});
    // Reopen another page on the same origin; no storage injection is used.
    const reopened=await context.newPage();await reopened.goto(`${origin}/app.html`);
    assert.equal(await reopened.getByLabel('Display name').inputValue(),'Reopened Name');
    await reopened.close();
    // Comparison-only pass over the starting app: capture/read geometry, no Save action.
    await capture('start.html','comparison-only.png');
    const after=Object.fromEntries(await Promise.all(files.map(async name=>[name,digest(await readFile(path.join(root,name)))])));
    assert.deepEqual(after,before,'Comparison/execution must not modify fixture app files');
    results.endingHashes=after;
    results.checks={V01:'Navigation bounds match; image review still required',V08:'Saved value restored after reload and new page',V12:'Read-only comparison capture; all fixture HTML hashes unchanged'};
    await page.evaluate(()=>localStorage.removeItem('display-name'));
    // Track the exact uncommitted skill state without inventing a commit ID.
    results.skillHashes=Object.fromEntries(await Promise.all(['SKILL.md','references/contract-and-comparison.md'].map(async name=>[name,digest(await readFile(path.join(root,'../..',name)))])));
  }
  await writeFile(path.join(root,phase==='reference'?'reference-run.json':'run-results.json'),JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify({phase,browser:results.browser,checks:results.checks??'Reference and starting captures created; not a behavior pass'}));
}finally{
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
}
