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
  out.textContent = JSON.stringify(data, null, 2);
}

document.getElementById('uploadBtn').addEventListener('click', uploadResume);
document.getElementById('matchBtn').addEventListener('click', matchJob);
