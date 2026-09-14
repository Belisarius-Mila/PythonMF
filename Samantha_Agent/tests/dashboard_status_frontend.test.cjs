const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/frontend/cockpit/app.js', 'utf8');
const names = ['renderDashboard','setDashboardPendingIfEmpty','dashboardValueIsPending','setDashboardValue','formatDashboardLoadedAt','dashboardStatusRank','dashboardStatusPriority','setDashboardStatusSignal','updateDashboardOverallStatus','escapeDashboardHtml'];
const functions = names.map(name => {
  const start = source.indexOf(`function ${name}(`);
  assert.ok(start >= 0, name);
  const rest = source.slice(start);
  const end = rest.slice(1).search(/\n\s*(?:async )?function \w+\(/);
  return end < 0 ? rest : rest.slice(0, end + 1);
}).join('\n');
const node = () => ({textContent:'',innerHTML:'',className:''});
function setup() {
  const state = {console,Date,dashboardStatusSignals:{},renderCodexApproval(){},classifyBackup:(_text,status)=>({className:status?.status==='ok'?'ok':'warn',label:status?.status==='ok'?'OK':'záloha chybí'})};
  for (const name of ['dashboardOverall','dashboardOverallLabel','dashboardOverallReason','dashboardDocuments','dashboardScanDocu','dashboardReminders','dashboardProjects','dashboardQuantitative','dashboardConsistency','dashboardQuickNotes','dashboardBackup','dashboardGit']) state[name]=node();
  const context=vm.createContext(state);vm.runInContext(functions,context);
  const healthy = {document_work:{summary:{new_pdf_count:0,review_pending_count:0,problem_count:0}},scandocu:{running:false},reminders:{counts:{active:0,open:0,conflicts:0}},git:{ok:true,dirty_count:0,ahead:0,behind:0},backup_status:{status:'ok'}};
  const render = data => {context.renderDashboard(data);for(const key of ['projects','consistency','quickNotes','decision']) context.setDashboardStatusSignal(key,'ok','Ověřeno');};
  return {context,healthy,render};
}
{
 const {context:c,healthy:h,render}=setup();h.document_work.summary.new_pdf_count=12;h.reminders.counts.active=4;h.git.ahead=6;render(h);
 c.setDashboardStatusSignal('quickNotes','work','3 aktivní poznámky');c.setDashboardStatusSignal('projects','work','Připomenout projekt');
 assert.equal(c.dashboardOverall.className,'dashboard-overall dashboard-overall-ok');
 for(const key of ['documents','reminders','git']) assert.equal(c.dashboardStatusSignals[key].level,'work');
 assert.match(c.dashboardOverallReason.textContent,/Co teď/);
 assert.ok(Number.isFinite(Date.parse(c.dashboardStatusSignals.documents.observedAt)));
 assert.ok(!('quantitative' in c.dashboardStatusSignals));
}
for(const [name,mutate,level,reason] of [
 ['document problem',h=>h.document_work.summary.problem_count=2,'warn',/Dokumenty/],
 ['reminder conflict',h=>h.reminders.counts.conflicts=1,'bad',/konflikt/],
 ['Git divergence',h=>{h.git.ahead=1;h.git.behind=1},'bad',/rozcházejí/],
 ['dirty Git',h=>h.git.dirty_count=1,'warn',/Git/],
 ['missing backup',h=>h.backup_status={status:'missing'},'warn',/Záloha/],
 ['missing documents',h=>delete h.document_work,'unknown',/nelze ověřit/],
 ['missing reminders',h=>delete h.reminders,'unknown',/nelze ověřit/],
 ['missing Git',h=>delete h.git,'unknown',/nelze zjistit/],
]) {const {context:c,healthy:h,render}=setup();mutate(h);render(h);assert.equal(c.dashboardOverall.className,`dashboard-overall dashboard-overall-${level}`,name);assert.match(c.dashboardOverallReason.textContent,reason,name);}
{
 const {context:c,healthy:h,render}=setup();render(h);c.setDashboardStatusSignal('decision','unknown','Frontu nelze ověřit');assert.match(c.dashboardOverallLabel.textContent,/není plně ověřený/);c.setDashboardStatusSignal('decision','ok','Obnoveno');assert.equal(c.dashboardOverall.className,'dashboard-overall dashboard-overall-ok');
 c.setDashboardStatusSignal('consistency','bad','Kritický nález');c.setDashboardStatusSignal('decision','unknown','Nedostupné');assert.match(c.dashboardOverallReason.textContent,/Kritický nález/);
}
console.log('Dashboard status: 10 behavior scenarios passed');
