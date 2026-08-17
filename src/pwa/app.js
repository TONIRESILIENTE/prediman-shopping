// app.js — Lógica do PWA PrediMan Shopping

// Token de serviço para o PWA (válido por 10 anos)
const DASHBOARD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYXNoQHByZWRpbWFuLmNvbSIsInBhcGVsIjoiYWRtaW4iLCJub21lIjoiRGFzaGJvYXJkIiwiZXhwIjoyMTAxOTAyNjI4LCJpYXQiOjE3ODY1NDI2Mjh9.0z0rphfFCNMn_Ix6eS2ofdMXykfGkiNkj211BJIn-1k";

// Configuração
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';

// Estado da aplicação
let ordens = [];
let ordemSelecionada = null;
let popCache = {};
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
  try {
    const resp = await fetch(url, {
      ...options,
      headers: { 
        'Content-Type': 'application/json', 
        'Authorization': 'Bearer ' + DASHBOARD_TOKEN,
        ...options.headers 
      },
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
  carregarOrdens();
});