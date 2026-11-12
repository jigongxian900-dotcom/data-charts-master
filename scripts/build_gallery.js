// Rebuild one canonical source, then synchronize the public offline gallery.
const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const root=path.resolve(__dirname,'..'),atlas=path.join(root,'examples/dashboard-atlas');
execFileSync(process.execPath,[path.join(atlas,'build_atlas.js')],{stdio:'inherit'});
fs.mkdirSync(path.join(root,'docs/labs'),{recursive:true});
fs.writeFileSync(path.join(root,'docs/index.html'),fs.readFileSync(path.join(atlas,'atlas.html'),'utf8').replaceAll('href="../interaction-lab/','href="labs/'));
fs.copyFileSync(path.join(atlas,'source-data.json'),path.join(root,'docs/source-data.json'));
for(const f of ['dir-1.html','dir-2.html','dir-3.html'])fs.copyFileSync(path.join(root,'examples/interaction-lab',f),path.join(root,'docs/labs',f));
for(const f of ['report.html','slides.html'])fs.copyFileSync(path.join(root,'examples/composed',f),path.join(root,'docs',f));
fs.copyFileSync(path.join(root,'examples/operating-story/report.html'),path.join(root,'docs/operating-story.html'));
const hosted=path.join(root,'docs/index.html');
fs.writeFileSync(hosted,fs.readFileSync(hosted,'utf8').replaceAll('href="../composed/','href="'));
fs.writeFileSync(hosted,fs.readFileSync(hosted,'utf8').replaceAll('href="../operating-story/report.html"','href="operating-story.html"'));
// Source examples and hosted copies each use the correct relative demo links.
console.log('Synchronized offline examples and public gallery.');
