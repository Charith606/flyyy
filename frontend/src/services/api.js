const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function seedSourceData(count = 50) {
  const res = await fetch(`${API_BASE}/seed?count=${count}`, { method: 'POST' });
  return res.json();
}

export async function fetchSourceCustomers(limit = 20) {
  const res = await fetch(`${API_BASE}/source-customers?limit=${limit}`);
  return res.json();
}

export async function runDiscovery() {
  const res = await fetch(`${API_BASE}/discovery/run`, { method: 'POST' });
  return res.json();
}

export async function fetchPolicies() {
  const res = await fetch(`${API_BASE}/policies`);
  return res.json();
}

export async function updatePolicy(fieldName, protectionType) {
  const res = await fetch(`${API_BASE}/policies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ field_name: fieldName, protection_type: protectionType, is_active: true })
  });
  return res.json();
}

export async function runBatchProtection(batchSize = 1000) {
  const res = await fetch(`${API_BASE}/batch/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ batch_size: batchSize })
  });
  return res.json();
}

export async function fetchBatches() {
  const res = await fetch(`${API_BASE}/batch/list`);
  return res.json();
}

export async function fetchProtectedCustomers(applyMasking = false) {
  const res = await fetch(`${API_BASE}/customers?limit=100&apply_ui_masking=${applyMasking}`);
  return res.json();
}

export async function sendCampaignEmail(recipientToken, campaignId, subject, body) {
  const res = await fetch(`${API_BASE}/gateway/send-campaign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recipient: recipientToken,
      campaign_id: campaignId,
      template_id: 'WELCOME_OFFER',
      subject: subject,
      body: body
    })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to send campaign');
  }
  return res.json();
}

export async function triggerBounceWebhook(email, reason = 'MAILBOX_NOT_FOUND') {
  const res = await fetch(`${API_BASE}/gateway/bounce-webhook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, event: 'BOUNCE', reason })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Bounce webhook failed');
  }
  return res.json();
}

export async function requestControlledReveal(subjectId, field, purpose, reference, actor) {
  const res = await fetch(`${API_BASE}/gateway/reveal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      subject_id: subjectId,
      field,
      purpose,
      reference,
      actor
    })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'ACCESS_DENIED');
  }
  return res.json();
}

export async function fetchAuditLogs(outcome = null, actor = null) {
  let url = `${API_BASE}/audit?limit=100`;
  if (outcome) url += `&outcome=${outcome}`;
  if (actor) url += `&actor=${actor}`;
  const res = await fetch(url);
  return res.json();
}
