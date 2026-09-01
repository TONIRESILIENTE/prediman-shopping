// app.js — Lógica do PWA PrediMan Shopping

// Token de serviço para o PWA (válido por 10 anos)
const DASHBOARD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYXNoQHByZWRpbWFuLmNvbSIsInBhcGVsIjoiYWRtaW4iLCJub21lIjoiRGFzaGJvYXJkIiwiZXhwIjoyMTAxOTAyNjI4LCJpYXQiOjE3ODY1NDI2Mjh9.0z0rphfFCNMn_Ix6eS2ofdMXykfGkiNkj211BJIn-1k";

// Configuração
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';

  // Token JWT
let token = null;

function mostrarLogin() {
  document.getElementById('login-screen').style.display = 'block';
  document.getElementById('app').innerHTML = '';
  document.getElementById('btn-logout').style.display = 'none';
}

async function fazerLogin() {
  const email = document.getElementById('login-email').value;
  const senha = document.getElementById('login-senha').value;
  const erroEl = document.getElementById('login-erro');
  
  erroEl.style.display = 'none';
  
  try {
    const resp = await fetch(API_URL + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, senha: senha }),
    });
    
    if (!resp.ok) {
      erroEl.textContent = 'Email ou senha incorretos';
      erroEl.style.display = 'block';
      return;
    }
    
    const data = await resp.json();
    token = data.access_token;
    
    // Esconde login e mostra app
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('btn-logout').style.display = 'block';
    
    carregarOrdens();
  } catch (err) {
    erroEl.textContent = 'Erro de conexão';
    erroEl.style.display = 'block';
  }
}

function fazerLogout() {
  token = null;
  localStorage.removeItem('prediman_token');
  ordens = [];
  mostrarLogin();
}

// Estado da aplicação
let ordens = [];
let ordemSelecionada = null;
let popCache = {};
let passosExecucao = {};
let online = navigator.onLine;

// Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/pwa/sw.js');
}

window.addEventListener('online', () => { online = true; atualizarStatusConexao(); });
window.addEventListener('offline', () => { online = false; atualizarStatusConexao(); });

function atualizarStatusConexao() {
  const el = document.getElementById('status-conexao');
  if (el) {
    el.textContent = online ? '🟢 Online' : '🔴 Offline';
    el.className = 'status ' + (online ? '' : 'offline');
  }
}

async function apiFetch(path, options = {}) {
  const url = API_URL + path;
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  
  try {
    const resp = await fetch(url, {
      ...options,
      headers: { ...headers, ...options.headers },
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    return await resp.json();
  } catch (err) {
    if (!online) {
      return JSON.parse(localStorage.getItem('ordens_cache') || '[]');
    }
    throw err;
  }
}

async function carregarOrdens() {
  try {
    ordens = await apiFetch('/ordens');
    localStorage.setItem('ordens_cache', JSON.stringify(ordens));
    renderizarListaOS();
  } catch (err) {
    document.getElementById('app').innerHTML = '<div class="empty-state"><div class="emoji">📡</div><p>Sem conexao com o servidor</p><button class="btn btn-iniciar" onclick="carregarOrdens()" style="margin-top:16px;width:auto">Tentar novamente</button></div>';
  }
}

function renderizarListaOS() {
  const pendentes = ordens.filter(o => o.status !== 'concluida');
  if (pendentes.length === 0) {
    document.getElementById('app').innerHTML = '<div class="empty-state"><div class="emoji">✅</div><p>Nenhuma OS pendente!</p></div>';
    return;
  }
  let html = '<div class="os-list">';
  pendentes.forEach(os => {
    const classe = os.severidade === 'critica' || os.severidade === 'alta' ? os.severidade : '';
    html += '<div class="os-card ' + classe + '" onclick="abrirOS(\'' + os.id + '\')"><div class="card-header"><span class="severidade ' + os.severidade + '">' + os.severidade + '</span><span style="font-size:11px;color:var(--text-secondary)">' + os.equipamento_id + '</span></div><h3>' + os.titulo + '</h3><p>📋 ' + (os.pop_codigo || 'Sem POP') + ' | ' + formatarStatus(os.status) + '</p></div>';
  });
  html += '</div>';
  document.getElementById('app').innerHTML = html;
}

function formatarStatus(status) {
  const mapa = { aberta: '📋 Aberta', em_andamento: '🔧 Em andamento', pausada: '⏸️ Pausada' };
  return mapa[status] || status;
}

async function abrirOS(id) {
  ordemSelecionada = ordens.find(o => o.id === id);
  if (!ordemSelecionada) return;

  await carregarPassos(id);
  renderizarDetalhes();
  if (ordemSelecionada.pop_codigo && !popCache[ordemSelecionada.pop_codigo]) {
    try {
      popCache[ordemSelecionada.pop_codigo] = await apiFetch('/pops/' + ordemSelecionada.pop_codigo);
    } catch (e) {
      console.log('POP nao carregado:', e);
    }
  }
  renderizarDetalhes();
}

function renderizarDetalhes() {
  const os = ordemSelecionada;
  const pop = os.pop_codigo ? popCache[os.pop_codigo] : null;
  let html = '<div class="detalhes"><h2>' + os.titulo + '</h2><div class="info-grid"><div class="info-item"><div class="label">Equipamento</div><div class="value">' + os.equipamento_id + '</div></div><div class="info-item"><div class="label">Severidade</div><div class="value" style="color:var(--' + (os.severidade === 'critica' || os.severidade === 'alta' ? 'danger' : 'warning') + ')">' + os.severidade.toUpperCase() + '</div></div><div class="info-item"><div class="label">Status</div><div class="value">' + formatarStatus(os.status) + '</div></div><div class="info-item"><div class="label">POP</div><div class="value">' + (os.pop_codigo || 'N/A') + '</div></div></div><p style="font-size:13px;color:var(--text-secondary)">' + os.descricao + '</p>';
  
  if (pop) {
    // Avatar + botão de narração
    html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">';
    html += '<div style="font-size:64px">🧑‍🔧</div>';
    html += '<div><button class="btn btn-iniciar" onclick="narrarPOP(popCache[\'' + pop.codigo + '\'])">🔊 Ouvir POP</button></div>';
    html += '</div>';
    
    // Animação Lottie
    if (pop.animacao_url) {
      html += '<div id="animacao-pop" style="width:100%;height:180px;margin-bottom:12px"></div>';
    }
    
    html += '<div class="pop-section"><h3>📖 Procedimento (' + pop.codigo + ')</h3><p style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">⏱️ ' + pop.tempo_estimado_minutos + ' min</p><h4 style="font-size:12px;margin-top:8px">🦺 EPIs:</h4><ul>' + pop.epis.map(e => '<li><span class="emoji">🦺</span>' + e + '</li>').join('') + '</ul><h4 style="font-size:12px;margin-top:8px">🔧 Ferramentas:</h4><ul>' + pop.ferramentas.map(f => '<li><span class="emoji">🔧</span>' + f + '</li>').join('') + '</ul><h4 style="font-size:12px;margin-top:8px">📋 Passos:</h4><ul>' + pop.passos.map(p => '<li><span class="emoji">▶️</span>' + p + '</li>').join('') + '</ul><h4 style="font-size:12px;margin-top:8px">⚠️ Riscos:</h4><ul class="riscos">' + pop.riscos.map(r => '<li><span class="emoji">⚠️</span>' + r + '</li>').join('') + '</ul></div>';
  }
    // Checklist de execução
  if (passosExecucao[os.id]) {
    const passos = passosExecucao[os.id];
    const concluidos = passos.filter(p => p.concluido).length;
    const percentual = Math.round((concluidos / passos.length) * 100);
    
    html += '<div class="pop-section">';
    html += '<h3>✅ Checklist de Execução</h3>';
    html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">';
    html += '<div style="flex:1;height:8px;background:var(--bg-primary);border-radius:4px;overflow:hidden">';
    html += '<div style="width:' + percentual + '%;height:100%;background:var(--success);border-radius:4px"></div>';
    html += '</div>';
    html += '<span style="font-size:12px;font-weight:600">' + percentual + '%</span>';
    html += '</div>';
    
    passos.forEach(p => {
      const statusIcon = p.concluido ? '✅' : '⏳';
      const bgColor = p.concluido ? 'rgba(46,204,113,0.1)' : 'transparent';
      
      html += '<div style="padding:10px;margin-bottom:8px;border-radius:8px;background:' + bgColor + '">';
      html += '<div style="display:flex;align-items:center;gap:8px">';
      html += '<span>' + statusIcon + '</span>';
      html += '<span style="flex:1;font-size:13px">' + p.numero_passo + '. ' + p.descricao + '</span>';
      if (!p.concluido) {
        html += '<button class="btn btn-iniciar" style="width:auto;padding:6px 12px;font-size:11px" onclick="marcarPasso(\'' + p.id + '\', \'' + os.id + '\')">Marcar</button>';
      }
      html += '</div>';
      if (p.foto_url) {
        html += '<div style="margin-top:6px;font-size:11px;color:var(--success)">📸 Foto anexada</div>';
      }
      html += '</div>';
    });
    
    html += '</div>';
  }
  
  html += '</div><div class="acoes"><button class="btn btn-voltar" onclick="voltarLista()">← Voltar</button>';
  
  if (os.status === 'aberta') {
    html += '<button class="btn btn-iniciar" onclick="atualizarStatus(\'' + os.id + '\', \'em_andamento\')">▶ Iniciar</button>';
  } else if (os.status === 'em_andamento') {
    html += '<button class="btn btn-pausar" onclick="atualizarStatus(\'' + os.id + '\', \'pausada\')">⏸ Pausar</button>';
    html += '<button class="btn btn-concluir" onclick="atualizarStatus(\'' + os.id + '\', \'concluida\')">✓ Concluir</button>';
  } else if (os.status === 'pausada') {
    html += '<button class="btn btn-iniciar" onclick="atualizarStatus(\'' + os.id + '\', \'em_andamento\')">▶ Retomar</button>';
    html += '<button class="btn btn-concluir" onclick="atualizarStatus(\'' + os.id + '\', \'concluida\')">✓ Concluir</button>';
  }
  
  html += '</div>';
  document.getElementById('app').innerHTML = html;

  // Inicia a animação Lottie
  if (pop && pop.animacao_url && window.lottie) {
    window.lottie.loadAnimation({
      container: document.getElementById('animacao-pop'),
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: pop.animacao_url,
    });
  }
}

function voltarLista() {
  ordemSelecionada = null;
  renderizarListaOS();
}

async function atualizarStatus(id, novoStatus) {
  try {
    await apiFetch('/ordens/' + id + '/status', {
      method: 'PATCH',
      body: JSON.stringify({ novo_status: novoStatus }),
    });
    const os = ordens.find(o => o.id === id);
    if (os) {
      os.status = novoStatus;
      if (novoStatus === 'concluida') {
        mostrarToast('✅ OS concluida com sucesso!');
        setTimeout(voltarLista, 1500);
      } else {
        mostrarToast('Status atualizado!');
        ordemSelecionada = os;
        renderizarDetalhes();
      }
    }
  } catch (err) {
    mostrarToast('❌ Erro ao atualizar. Tente novamente.', true);
  }
}

function mostrarToast(mensagem, erro) {
  erro = erro || false;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.background = erro ? 'var(--danger)' : 'var(--success)';
  toast.textContent = mensagem;
  document.body.appendChild(toast);
  setTimeout(function() { toast.remove(); }, 2000);
}

async function carregarPassos(ordemId) {
  try {
    passosExecucao[ordemId] = await apiFetch('/os/' + ordemId + '/passos');
  } catch (e) {
    passosExecucao[ordemId] = [];
  }
}

async function gerarPassos(ordemId) {
  try {
    await apiFetch('/os/' + ordemId + '/passos/gerar', { method: 'POST' });
    await carregarPassos(ordemId);
    renderizarDetalhes();
  } catch (e) {
    mostrarToast('Erro ao gerar passos', true);
  }
}



function narrarPOP(pop) {
  if (!('speechSynthesis' in window)) {
    mostrarToast('❌ Narração não suportada neste aparelho', true);
    return;
  }
  
  // Cancela narração anterior
  window.speechSynthesis.cancel();
  
  // Monta texto para narrar
  let texto = 'Procedimento: ' + pop.titulo + '. ';
  texto += 'Tempo estimado: ' + pop.tempo_estimado_minutos + ' minutos. ';
  texto += 'EPIs obrigatórios: ' + pop.epis.join(', ') + '. ';
  texto += 'Passos: ' + pop.passos.join('. ') + '. ';
  texto += 'Riscos: ' + pop.riscos.join('. ');
  
  const utterance = new SpeechSynthesisUtterance(texto);
  utterance.lang = 'pt-BR';
  utterance.rate = 0.9;
  
  window.speechSynthesis.speak(utterance);
  mostrarToast('🔊 Narrando POP...');
}

document.addEventListener('DOMContentLoaded', function() {
  atualizarStatusConexao();
  
  // Verifica se há token salvo
  const tokenSalvo = localStorage.getItem('prediman_token');
  if (tokenSalvo) {
    token = tokenSalvo;
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('btn-logout').style.display = 'block';
    carregarOrdens();
  } else {
    mostrarLogin();
  }
});