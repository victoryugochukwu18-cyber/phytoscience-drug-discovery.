
import os
import re
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# RDKit powers chemical structure analysis.
# The website can still start if RDKit is unavailable.
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phytoscience Drug Discovery Suite</title>
<style>
:root {
  --bg:#f4f7fb; --panel:#ffffff; --text:#17233b;
  --muted:#65748b; --primary:#176b55; --line:#e0e7ef;
  --soft:#e5f5ed; --nav:#102d29;
}
* { box-sizing:border-box; }
body {
  margin:0; font-family:Arial,sans-serif;
  background:var(--bg); color:var(--text);
}
header {
  background:var(--nav); color:white; padding:17px;
  position:sticky; top:0; z-index:5;
}
.brand { font-size:20px; font-weight:bold; }
.tagline { font-size:12px; color:#c5ddd6; margin-top:5px; }
.layout { display:flex; min-height:100vh; }
nav {
  width:235px; flex-shrink:0; background:#183b35;
  padding:14px 10px; color:white;
}
nav button {
  display:block; width:100%; text-align:left;
  background:transparent; color:#e2eee9;
  border:0; padding:12px 10px; margin:3px 0;
  border-radius:8px; cursor:pointer; font-size:14px;
}
nav button.active, nav button:hover { background:#2c5d50; }
main { padding:22px; width:100%; min-width:0; }
h1 { font-size:25px; margin:0 0 8px; }
h2 { font-size:18px; margin-top:0; }
p { line-height:1.55; }
.muted { color:var(--muted); font-size:13px; }
.cards {
  display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px; margin:22px 0;
}
.card,.panel {
  background:var(--panel); border:1px solid var(--line);
  border-radius:13px; padding:17px; margin-bottom:14px;
}
.metric { font-size:27px; font-weight:bold; margin:9px 0; }
.icon { font-size:24px; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
button.primary {
  background:var(--primary); color:white; border:0;
  padding:11px 15px; border-radius:8px; cursor:pointer;
}
button.secondary {
  background:#e8eef5; color:var(--text); border:0;
  padding:10px 13px; border-radius:8px; cursor:pointer;
}
input,textarea,select {
  width:100%; padding:12px; margin:7px 0 13px;
  border:1px solid #cbd5e1; border-radius:8px;
  background:white; color:#17233b; font-size:14px;
}
textarea { min-height:105px; resize:vertical; }
label { font-weight:bold; font-size:13px; }
.result {
  padding:13px; border-radius:8px; background:#f0f6f4;
  overflow-wrap:anywhere; margin-top:12px;
}
.tag {
  display:inline-block; background:var(--soft);
  color:#17583e; padding:5px 9px; border-radius:20px;
  font-size:12px; margin:3px 3px 3px 0;
}
.warning { background:#fff5dc; padding:12px; border-radius:8px; }
table { width:100%; border-collapse:collapse; font-size:13px; }
td,th { padding:10px 6px; border-bottom:1px solid var(--line); text-align:left; }
.hidden { display:none; }
.module-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
.module-link {
  padding:15px; background:white; border:1px solid var(--line);
  border-radius:10px; cursor:pointer;
}
.module-link strong { display:block; margin-bottom:7px; }
footer { color:var(--muted); font-size:12px; padding:12px 0; }
@media(max-width:760px) {
  .layout { display:block; }
  nav { width:100%; display:flex; overflow-x:auto; gap:5px; }
  nav button { min-width:max-content; width:auto; }
  main { padding:14px; }
  .cards { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .grid2,.module-list { grid-template-columns:1fr; }
  h1 { font-size:22px; }
}
</style>
</head>
<body>
<header>
  <div class="brand">🧬 Phytoscience Drug Discovery Suite</div>
  <div class="tagline">Bioinformatics · Cheminformatics · Computational Drug Discovery</div>
</header>

<div class="layout">
<nav id="nav">
  <button class="active" data-page="dashboard">🏠 Dashboard</button>
  <button data-page="projects">📁 Research Projects</button>
  <button data-page="bioinformatics">🧬 Bioinformatics</button>
  <button data-page="smiles">⚗️ SMILES Analyzer</button>
  <button data-page="cheminformatics">🔬 Cheminformatics</button>
  <button data-page="compounds">🧪 Compound Library</button>
  <button data-page="targets">🎯 Protein Targets</button>
  <button data-page="docking">🔗 Molecular Docking</button>
  <button data-page="admet">🛡️ ADMET & Toxicity</button>
  <button data-page="machine">🤖 Machine Learning</button>
  <button data-page="natural">🌿 Natural Products</button>
  <button data-page="reports">📊 Reports</button>
</nav>

<main>
<section id="dashboard" class="page">
  <h1>Research Dashboard</h1>
  <p class="muted">Your integrated workspace for computational drug discovery.</p>
  <div class="cards">
    <div class="card"><div class="icon">🧪</div><div class="muted">Saved Compounds</div><div class="metric" id="compoundCount">0</div></div>
    <div class="card"><div class="icon">🧬</div><div class="muted">Sequence Checks</div><div class="metric" id="sequenceCount">0</div></div>
    <div class="card"><div class="icon">🎯</div><div class="muted">Protein Targets</div><div class="metric" id="targetCount">0</div></div>
    <div class="card"><div class="icon">📁</div><div class="muted">Research Projects</div><div class="metric" id="projectCount">0</div></div>
  </div>
  <div class="panel">
    <h2>Start a new analysis</h2>
    <div class="module-list">
      <div class="module-link" onclick="showPage('smiles')"><strong>⚗️ Analyze a SMILES</strong><span class="muted">Validate a molecule and calculate properties.</span></div>
      <div class="module-link" onclick="showPage('bioinformatics')"><strong>🧬 Analyze a sequence</strong><span class="muted">Check a protein or DNA FASTA sequence.</span></div>
      <div class="module-link" onclick="showPage('compounds')"><strong>🧪 Compound library</strong><span class="muted">Save compounds in this browser.</span></div>
      <div class="module-link" onclick="showPage('natural')"><strong>🌿 Natural products</strong><span class="muted">Organize medicinal plant research.</span></div>
    </div>
  </div>
  <div class="panel">
    <h2>Scientific workflow</h2>
    <p>
      <span class="tag">1. Compound identification</span>
      <span class="tag">2. SMILES validation</span>
      <span class="tag">3. Protein target selection</span>
      <span class="tag">4. Docking</span>
      <span class="tag">5. ADMET</span>
      <span class="tag">6. Candidate review</span>
    </p>
    <p class="muted">A docking score or predicted property alone cannot establish drug efficacy or safety.</p>
  </div>
</section>

<section id="projects" class="page hidden">
  <h1>Research Projects</h1>
  <p class="muted">Create project records to organize your research.</p>
  <div class="panel">
    <label>Project name</label><input id="projectName" placeholder="e.g. Moringa antimalarial research">
    <label>Research objective</label><textarea id="projectObjective" placeholder="Describe the question you want to investigate"></textarea>
    <button class="primary" onclick="addProject()">Save project</button>
    <div id="projectMessage"></div>
  </div>
  <div class="panel"><h2>Saved projects</h2><div id="projectList">No projects saved yet.</div></div>
</section>

<section id="bioinformatics" class="page hidden">
  <h1>Bioinformatics Laboratory</h1>
  <p class="muted">Basic sequence validation and statistics.</p>
  <div class="panel">
    <label>Paste a FASTA sequence</label>
    <textarea id="fastaInput" placeholder=">Example_protein&#10;MKWVTFISLLFLFSSAYS"></textarea>
    <label>Sequence type</label>
    <select id="sequenceType"><option value="protein">Protein</option><option value="dna">DNA</option><option value="rna">RNA</option></select>
    <button class="primary" onclick="analyzeFasta()">Check sequence</button>
    <div id="fastaResult"></div>
  </div>
  <div class="panel">
    <h2>Future integrations</h2>
    <span class="tag">BLAST</span><span class="tag">UniProt</span><span class="tag">PDB structures</span><span class="tag">Sequence alignment</span><span class="tag">Target identification</span>
    <p class="muted">These external searches and advanced analyses need their own integrations.</p>
  </div>
</section>

<section id="smiles" class="page hidden">
  <h1>SMILES Analyzer</h1>
  <p class="muted">Enter a chemical SMILES string to validate the structure and calculate molecular descriptors.</p>
  <div class="panel">
    <label>Compound name (optional)</label><input id="smilesName" placeholder="e.g. Quercetin">
    <label>SMILES string</label><textarea id="smilesInput" placeholder="Paste a SMILES string here"></textarea>
    <button class="primary" onclick="analyzeSmiles()">Analyze molecule</button>
    <button class="secondary" onclick="document.getElementById('smilesInput').value='O=c1c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c2c1O'">Load quercetin example</button>
    <div id="smilesResult"></div>
  </div>
</section>

<section id="cheminformatics" class="page hidden">
  <h1>Cheminformatics Laboratory</h1>
  <div class="module-list">
    <div class="module-link" onclick="showPage('smiles')"><strong>SMILES validation</strong><span class="muted">Parse chemical notation.</span></div>
    <div class="module-link" onclick="showPage('smiles')"><strong>Molecular descriptors</strong><span class="muted">Weight, LogP, TPSA and more.</span></div>
    <div class="module-link"><strong>Fingerprints and similarity</strong><span class="muted">Planned RDKit Morgan fingerprint and Tanimoto search.</span></div>
    <div class="module-link"><strong>Structure visualization</strong><span class="muted">Interactive 2D and 3D rendering to be integrated.</span></div>
  </div>
  <div class="panel"><h2>Supported formats to add</h2><p>SDF · MOL · MOL2 · PDB · PDBQT</p><p class="muted">File support depends on the selected scientific engine and format.</p></div>
</section>

<section id="compounds" class="page hidden">
  <h1>Compound Library</h1>
  <p class="muted">Records are saved in this browser, not in a shared cloud database.</p>
  <div class="panel">
    <label>Compound name</label><input id="compoundName" placeholder="Compound name">
    <label>SMILES</label><input id="compoundSmiles" placeholder="SMILES string">
    <label>Source / plant</label><input id="compoundSource" placeholder="e.g. Moringa oleifera leaf">
    <button class="primary" onclick="saveCompound()">Save compound</button>
    <div id="compoundMessage"></div>
  </div>
  <div class="panel"><h2>Saved compounds</h2><div id="compoundList">No compounds saved yet.</div></div>
</section>

<section id="targets" class="page hidden">
  <h1>Protein Targets</h1>
  <p class="muted">Organize target records before performing docking.</p>
  <div class="panel">
    <label>Target name</label><input id="targetName" placeholder="e.g. PfDHFR-TS">
    <label>Protein identifier / PDB ID</label><input id="targetId" placeholder="e.g. a PDB ID or UniProt accession">
    <label>Disease or biological question</label><input id="targetDisease" placeholder="e.g. malaria">
    <button class="primary" onclick="saveTarget()">Save target record</button>
    <div id="targetMessage"></div>
  </div>
  <div class="panel"><h2>Target records</h2><div id="targetList">No targets saved yet.</div></div>
  <div class="warning">A saved target record does not mean the target has been biologically validated.</div>
</section>

<section id="docking" class="page hidden">
  <h1>Molecular Docking</h1>
  <div class="panel">
    <h2>Docking workspace</h2>
    <p>Planned integration: protein preparation, ligand preparation, binding-site coordinates, AutoDock Vina execution, pose analysis, and interaction visualization.</p>
    <label>Compound</label><input id="dockCompound" placeholder="Compound name">
    <label>Protein target</label><input id="dockTarget" placeholder="Protein name">
    <label>Docking score (kcal/mol), if already calculated</label><input id="dockScore" type="number" step="0.001" placeholder="Enter an existing score">
    <button class="primary" onclick="saveDocking()">Save existing result</button>
    <div id="dockingResult"></div>
  </div>
  <div class="warning">This form records a score you already obtained elsewhere. It does not run molecular docking.</div>
  <div class="panel"><h2>Saved docking records</h2><div id="dockingList">No docking results saved.</div></div>
</section>

<section id="admet" class="page hidden">
  <h1>ADMET & Toxicity</h1>
  <div class="panel">
    <h2>Prediction workspace</h2>
    <p>Future integrations may include validated prediction services or locally hosted models for solubility, absorption, distribution, metabolism, excretion and toxicity.</p>
    <label>Compound name</label><input id="admetCompound" placeholder="Compound name">
    <label>Prediction source</label><input id="admetSource" placeholder="e.g. name of tool or published model">
    <label>Result / notes</label><textarea id="admetNotes" placeholder="Record an existing prediction and its limitations"></textarea>
    <button class="primary" onclick="saveAdmet()">Save existing result</button>
    <div id="admetMessage"></div>
  </div>
  <div class="warning">No ADMET prediction is performed by this form. Predicted toxicity is not proof of safety.</div>
  <div class="panel"><h2>Saved ADMET records</h2><div id="admetList">No records saved.</div></div>
</section>

<section id="machine" class="page hidden">
  <h1>Machine Learning</h1>
  <div class="panel"><h2>Model development workspace</h2>
    <p>Future capabilities: dataset curation, molecular fingerprints, classification, regression, cross-validation, external test sets and model interpretation.</p>
    <span class="tag">scikit-learn</span><span class="tag">RDKit</span><span class="tag">DeepChem</span><span class="tag">PyTorch</span>
    <p class="muted">A predictive model requires suitable training data, validation, and an assessment of uncertainty before research use.</p>
  </div>
</section>

<section id="natural" class="page hidden">
  <h1>Natural Products Research</h1>
  <div class="panel"><h2>Plant research record</h2>
    <label>Scientific plant name</label><input id="plantName" placeholder="e.g. Moringa oleifera">
    <label>Plant part</label><select id="plantPart"><option>Leaf</option><option>Stem bark</option><option>Root</option><option>Seed</option><option>Flower</option><option>Fruit</option><option>Whole plant</option><option>Other</option></select>
    <label>Phytochemical / compound</label><input id="plantCompound" placeholder="e.g. Quercetin">
    <label>Reference or notes</label><textarea id="plantNotes" placeholder="Add a paper DOI, URL, or experimental notes"></textarea>
    <button class="primary" onclick="savePlant()">Save plant record</button>
    <div id="plantMessage"></div>
  </div>
  <div class="panel"><h2>Plant records</h2><div id="plantList">No plant records saved.</div></div>
</section>

<section id="reports" class="page hidden">
  <h1>Research Reports</h1>
  <div class="panel"><h2>Research summary</h2><p>Generate a basic summary of records saved in this browser.</p>
    <button class="primary" onclick="makeReport()">Generate summary</button>
    <button class="secondary" onclick="exportData()">Export records as JSON</button>
    <div id="reportResult"></div>
  </div>
  <div class="panel"><h2>Research quality checklist</h2>
    <p>☐ Confirm compound identity and stereochemistry.</p>
    <p>☐ Record database identifiers and literature references.</p>
    <p>☐ Check protein structure quality and preparation.</p>
    <p>☐ Record software versions and analysis settings.</p>
    <p>☐ Distinguish predictions from experimental findings.</p>
  </div>
</section>

<footer>PDDS prototype · Keep research data backed up · Computational predictions require scientific validation.</footer>
</main>
</div>

<script>
const keys = ["compounds","projects","targets","dockings","admet","plants"];
function read(key) {
  try { return JSON.parse(localStorage.getItem("pdds_"+key) || "[]"); }
  catch(e) { return []; }
}
function write(key, value) {
  localStorage.setItem("pdds_"+key, JSON.stringify(value));
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  })[c]);
}
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  document.querySelectorAll("#nav button").forEach(b =>
    b.classList.toggle("active", b.dataset.page === id));
  refresh();
  window.scrollTo(0,0);
}
document.querySelectorAll("#nav button").forEach(b =>
  b.addEventListener("click", () => showPage(b.dataset.page)));

function renderList(id, records, fields) {
  const el = document.getElementById(id);
  if (!records.length) { el.textContent = "No records saved yet."; return; }
  el.innerHTML = "<div style='overflow-x:auto'><table><thead><tr>" +
    fields.map(f => "<th>"+escapeHtml(f[1])+"</th>").join("") +
    "<th>Action</th></tr></thead><tbody>" +
    records.map((r,i) => "<tr>" +
      fields.map(f => "<td>"+escapeHtml(r[f[0]])+"</td>").join("") +
      "<td><button class='secondary' onclick=\"removeRecord('"+escapeHtml(id)+"',"+i+")\">Delete</button></td></tr>"
    ).join("") + "</tbody></table></div>";
}
const listMap = {
  "compoundList":["compounds",[["name","Name"],["smiles","SMILES"],["source","Source"]]],
  "projectList":["projects",[["name","Project"],["objective","Objective"]]],
  "targetList":["targets",[["name","Target"],["id","Identifier"],["disease","Question"]]],
  "dockingList":["dockings",[["compound","Compound"],["target","Target"],["score","Score"]]],
  "admetList":["admet",[["compound","Compound"],["source","Source"],["notes","Notes"]]],
  "plantList":["plants",[["plant","Plant"],["part","Part"],["compound","Compound"],["notes","Reference / notes"]]]
};
function removeRecord(listId, index) {
  const [key] = listMap[listId];
  const data = read(key); data.splice(index,1); write(key,data); refresh();
}
function addProject() {
  const name = document.getElementById("projectName").value.trim();
  if (!name) return alert("Enter a project name.");
  const data=read("projects");
  data.push({name,objective:document.getElementById("projectObjective").value.trim()});
  write("projects",data);
  document.getElementById("projectMessage").textContent="Project saved in this browser.";
  document.getElementById("projectName").value="";
  document.getElementById("projectObjective").value="";
  refresh();
}
function saveCompound() {
  const name=document.getElementById("compoundName").value.trim();
  const smiles=document.getElementById("compoundSmiles").value.trim();
  if(!name || !smiles) return alert("Enter both a compound name and SMILES.");
  const data=read("compounds");
  data.push({name,smiles,source:document.getElementById("compoundSource").value.trim()});
  write("compounds",data);
  document.getElementById("compoundMessage").textContent="Compound record saved. Use SMILES Analyzer to check its structure.";
  refresh();
}
function saveTarget() {
  const name=document.getElementById("targetName").value.trim();
  if(!name) return alert("Enter a target name.");
  const data=read("targets");
  data.push({name,id:document.getElementById("targetId").value.trim(),disease:document.getElementById("targetDisease").value.trim()});
  write("targets",data);
  document.getElementById("targetMessage").textContent="Target record saved.";
  refresh();
}
function saveDocking() {
  const compound=document.getElementById("dockCompound").value.trim();
  const target=document.getElementById("dockTarget").value.trim();
  const score=document.getElementById("dockScore").value;
  if(!compound || !target || score==="") return alert("Enter compound, target, and an existing score.");
  const data=read("dockings"); data.push({compound,target,score:score+" kcal/mol"});
  write("dockings",data);
  document.getElementById("dockingResult").textContent="Existing docking result recorded; no docking was run here.";
  refresh();
}
function saveAdmet() {
  const compound=document.getElementById("admetCompound").value.trim();
  if(!compound) return alert("Enter a compound name.");
  const data=read("admet");
  data.push({compound,source:document.getElementById("admetSource").value.trim(),notes:document.getElementById("admetNotes").value.trim()});
  write("admet",data);
  document.getElementById("admetMessage").textContent="Existing ADMET notes saved.";
  refresh();
}
function savePlant() {
  const plant=document.getElementById("plantName").value.trim();
  if(!plant) return alert("Enter a scientific plant name.");
  const data=read("plants");
  data.push({plant,part:document.getElementById("plantPart").value,compound:document.getElementById("plantCompound").value.trim(),notes:document.getElementById("plantNotes").value.trim()});
  write("plants",data);
  document.getElementById("plantMessage").textContent="Plant record saved.";
  refresh();
}
async function analyzeSmiles() {
  const smiles=document.getElementById("smilesInput").value.trim();
  const name=document.getElementById("smilesName").value.trim();
  const result=document.getElementById("smilesResult");
  if(!smiles) { result.textContent="Enter a SMILES string first."; return; }
  result.textContent="Analyzing...";
  try {
    const response=await fetch("/api/smiles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({smiles})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error || "Analysis failed");
    if(!data.valid) { result.innerHTML="<div class='warning'>"+escapeHtml(data.error)+"</div>"; return; }
    result.innerHTML="<div class='result'><strong>Structure validated</strong><br>"+
      Object.entries(data.properties).map(([k,v])=>"<p><b>"+escapeHtml(k)+":</b> "+escapeHtml(v)+"</p>").join("")+
      "<p><b>Canonical SMILES:</b><br>"+escapeHtml(data.canonical_smiles)+"</p>"+
      "<button class='primary' onclick='saveAnalyzedCompound()'>Save to compound library</button></div>";
    window.lastAnalyzed={name:name || "Unnamed compound",smiles:data.canonical_smiles};
  } catch(e) { result.textContent="Error: "+e.message; }
}
function saveAnalyzedCompound() {
  if(!window.lastAnalyzed) return;
  const data=read("compounds");
  data.push({name:window.lastAnalyzed.name,smiles:window.lastAnalyzed.smiles,source:"SMILES Analyzer"});
  write("compounds",data); refresh();
  document.getElementById("smilesResult").insertAdjacentHTML("beforeend","<p>Saved in this browser.</p>");
}
async function analyzeFasta() {
  const sequence=document.getElementById("fastaInput").value.trim();
  const type=document.getElementById("sequenceType").value;
  const result=document.getElementById("fastaResult");
  result.textContent="Checking sequence...";
  try {
    const response=await fetch("/api/fasta",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sequence,type})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error || "Check failed");
    if(!data.valid) { result.innerHTML="<div class='warning'>"+escapeHtml(data.error)+"</div>"; return; }
    result.innerHTML="<div class='result'><b>Sequence format looks valid</b>"+
      Object.entries(data.statistics).map(([k,v])=>"<p><b>"+escapeHtml(k)+":</b> "+escapeHtml(v)+"</p>").join("")+
      "<p class='muted'>This is basic sequence validation, not target identification or a BLAST search.</p></div>";
    const n=Number(localStorage.getItem("pdds_sequence_count")||0)+1;
    localStorage.setItem("pdds_sequence_count",String(n)); refresh();
  } catch(e) { result.textContent="Error: "+e.message; }
}
function makeReport() {
  const summary=Object.fromEntries(keys.map(k=>[k,read(k).length]));
  document.getElementById("reportResult").innerHTML="<div class='result'><pre>"+escapeHtml(JSON.stringify(summary,null,2))+"</pre></div>";
}
function exportData() {
  const all=Object.fromEntries(keys.map(k=>[k,read(k)]));
  const blob=new Blob([JSON.stringify(all,null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download="pdds-research-records.json"; a.click();
  URL.revokeObjectURL(url);
}
function refresh() {
  document.getElementById("compoundCount").textContent=read("compounds").length;
  document.getElementById("projectCount").textContent=read("projects").length;
  document.getElementById("targetCount").textContent=read("targets").length;
  document.getElementById("sequenceCount").textContent=localStorage.getItem("pdds_sequence_count")||"0";
  for(const [id,[key,fields]] of Object.entries(listMap)) renderList(id,read(key),fields);
}
refresh();
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "Phytoscience Drug Discovery Suite",
        "rdkit_available": RDKIT_AVAILABLE
    })


@app.route("/api/smiles", methods=["POST"])
def analyze_smiles():
    data = request.get_json(silent=True) or {}
    smiles = str(data.get("smiles", "")).strip()

    if not smiles:
        return jsonify({"valid": False, "error": "Enter a SMILES string."}), 400

    if len(smiles) > 5000:
        return jsonify({"valid": False, "error": "SMILES input is too long."}), 400

    if not RDKIT_AVAILABLE:
        return jsonify({
            "valid": False,
            "error": "RDKit is not installed. Check the Render build logs."
        }), 503

    try:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            return jsonify({
                "valid": False,
                "error": "RDKit could not parse this SMILES string."
            }), 400

        canonical = Chem.MolToSmiles(molecule)
        properties = {
            "Molecular weight (g/mol)": round(Descriptors.MolWt(molecule), 3),
            "LogP (calculated)": round(Descriptors.MolLogP(molecule), 3),
            "TPSA (Å²)": round(Descriptors.TPSA(molecule), 3),
            "Hydrogen-bond donors": Lipinski.NumHDonors(molecule),
            "Hydrogen-bond acceptors": Lipinski.NumHAcceptors(molecule),
            "Rotatable bonds": Lipinski.NumRotatableBonds(molecule),
            "Heavy atoms": molecule.GetNumHeavyAtoms(),
            "Ring count": rdMolDescriptors.CalcNumRings(molecule),
            "Lipinski Rule of Five": (
                "No more than one violation"
                if (
                    Descriptors.MolWt(molecule) <= 500
                    and Descriptors.MolLogP(molecule) <= 5
                    and Lipinski.NumHDonors(molecule) <= 5
                    and Lipinski.NumHAcceptors(molecule) <= 10
                )
                else "One or more property limits exceeded"
            )
        }

        return jsonify({
            "valid": True,
            "canonical_smiles": canonical,
            "properties": properties
        })

    except Exception:
        app.logger.exception("SMILES analysis failed")
        return jsonify({
            "valid": False,
            "error": "Could not analyze this molecule."
        }), 400


@app.route("/api/fasta", methods=["POST"])
def analyze_fasta():
    data = request.get_json(silent=True) or {}
    sequence_text = str(data.get("sequence", "")).strip()
    sequence_type = str(data.get("type", "protein")).lower()

    if not sequence_text:
        return jsonify({"valid": False, "error": "Enter a sequence."}), 400

    lines = [
        line.strip() for line in sequence_text.splitlines()
        if line.strip() and not line.strip().startswith(";")
    ]

    if lines and lines[0].startswith(">"):
        lines = lines[1:]

    sequence = re.sub(r"\s+", "", "".join(lines)).upper()

    if not sequence:
        return jsonify({
            "valid": False,
            "error": "No sequence was found after the FASTA header."
        }), 400

    if len(sequence) > 1000000:
        return jsonify({
            "valid": False,
            "error": "Sequence is too long for this basic checker."
        }), 400

    alphabets = {
        "dna": set("ACGTN"),
        "rna": set("ACGUN"),
        "protein": set("ACDEFGHIKLMNPQRSTVWYBXZJUO*")
    }

    if sequence_type not in alphabets:
        return jsonify({"valid": False, "error": "Unknown sequence type."}), 400

    invalid = sorted(set(sequence) - alphabets[sequence_type])
    if invalid:
        return jsonify({
            "valid": False,
            "error": "Invalid character(s) for " + sequence_type + ": "
                     + ", ".join(invalid)
        }), 400

    statistics = {
        "Sequence type": sequence_type.upper(),
        "Length": len(sequence),
        "Characters found": len(set(sequence))
    }

    if sequence_type in ("dna", "rna"):
        statistics["GC content (%)"] = round(
            100 * sum(c in "GC" for c in sequence) / len(sequence), 2
        )

    return jsonify({"valid": True, "statistics": statistics})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
