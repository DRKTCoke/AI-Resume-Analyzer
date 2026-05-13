let currentResumeId = null;

async function uploadResume() {
  const apiBase = document.getElementById('apiBase').value.trim();
  const fileInput = document.getElementById('file');
  const out = document.getElementById('uploadResult');

  if (!fileInput.files.length) {
    out.textContent = '请先选择 PDF 文件';
    return;
  }

  const form = new FormData();
  form.append('file', fileInput.files[0]);

  const res = await fetch(`${apiBase}/api/resume/upload`, { method: 'POST', body: form });
  const data = await res.json();
  if (!res.ok) {
    out.textContent = JSON.stringify(data, null, 2);
    return;
  }

  currentResumeId = data.resume_id;
  out.textContent = JSON.stringify(data, null, 2);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderList(items) {
  const values = Array.isArray(items) && items.length ? items : ['暂无'];
  return `<ul>${values.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
}

function renderMatchResult(data, response) {
  const out = document.getElementById('matchResult');

  if (!response.ok) {
    out.innerHTML = `<pre class="error">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    return;
  }

  const analysis = data.analysis || {};
  const breakdown = data.breakdown || {};
  const score = Number(data.total_score || 0);
  const scorePercent = Math.round(score * 100);
  const replayed = response.headers.get('Idempotency-Replayed') === 'true';
  const requestId = response.headers.get('X-Request-ID');

  out.innerHTML = `
    <div class="score-row">
      <div>
        <div class="score-value">${scorePercent}</div>
        <div class="score-label">匹配分</div>
      </div>
      <div class="score-main">
        <div class="level">${escapeHtml(analysis.match_level || '待评估')}</div>
        <p>${escapeHtml(analysis.summary || '')}</p>
        <div class="score-track"><span style="width: ${Math.max(0, Math.min(100, scorePercent))}%"></span></div>
      </div>
    </div>

    <div class="metric-grid">
      <div><strong>${Math.round((breakdown.keyword_match_rate || 0) * 100)}%</strong><span>关键词</span></div>
      <div><strong>${Math.round((breakdown.experience_score || 0) * 100)}%</strong><span>经验</span></div>
      <div><strong>${Math.round((breakdown.education_score || 0) * 100)}%</strong><span>学历</span></div>
      <div><strong>${Math.round((breakdown.intent_score || 0) * 100)}%</strong><span>意向</span></div>
    </div>

    <div class="tag-row">
      ${(breakdown.matched_keywords || []).map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join('') || '<span>暂无命中关键词</span>'}
    </div>

    <div class="analysis-grid">
      <div class="analysis-block">
        <h3>候选人优势</h3>
        ${renderList(analysis.strengths)}
      </div>
      <div class="analysis-block">
        <h3>风险点</h3>
        ${renderList(analysis.risks)}
      </div>
      <div class="analysis-block">
        <h3>优化建议</h3>
        ${renderList(analysis.suggestions)}
      </div>
      <div class="analysis-block">
        <h3>面试关注点</h3>
        ${renderList(analysis.interview_focus)}
      </div>
    </div>

    <div class="meta-row">
      <span>resume_id: ${escapeHtml(data.resume_id)}</span>
      ${requestId ? `<span>request_id: ${escapeHtml(requestId)}</span>` : ''}
      ${replayed ? '<span>cache: replayed</span>' : ''}
    </div>
  `;
}

async function matchJob() {
  const apiBase = document.getElementById('apiBase').value.trim();
  const jdText = document.getElementById('jdText').value;
  const out = document.getElementById('matchResult');

  if (!currentResumeId) {
    out.textContent = '请先上传并解析简历';
    return;
  }

  const res = await fetch(`${apiBase}/api/job/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: currentResumeId, jd_text: jdText })
  });

  const data = await res.json();
  renderMatchResult(data, res);
}

document.getElementById('uploadBtn').addEventListener('click', uploadResume);
document.getElementById('matchBtn').addEventListener('click', matchJob);
