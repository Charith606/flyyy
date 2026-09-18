import React, { useState, useEffect } from 'react';
import { Mail, Send, RefreshCw, CheckCircle, AlertOctagon, CornerDownRight, ArrowRight } from 'lucide-react';
import { fetchProtectedCustomers, sendCampaignEmail, triggerBounceWebhook } from '../services/api';

export default function MarketingGatewayDemo() {
  const [customers, setCustomers] = useState([]);
  const [selectedToken, setSelectedToken] = useState('');
  const [campaignId, setCampaignId] = useState('CMP1001');
  const [subject, setSubject] = useState('Exclusive Flyyy 50% Off Offer');
  const [body, setBody] = useState('Hello! Your exclusive discount code is FLYYY50.');
  const [sendResult, setSendResult] = useState(null);
  const [sending, setSending] = useState(false);

  // Bounce simulation state
  const [bounceEmail, setBounceEmail] = useState('john@example.com');
  const [bounceResult, setBounceResult] = useState(null);
  const [bouncing, setBouncing] = useState(false);

  useEffect(() => {
    fetchProtectedCustomers(false).then((res) => {
      const items = res.items || [];
      setCustomers(items);
      if (items.length > 0) {
        setSelectedToken(items[0].email_token);
      }
    });
  }, []);

  const handleSendCampaign = async (e) => {
    e.preventDefault();
    if (!selectedToken) return;
    setSending(true);
    setSendResult(null);
    try {
      const res = await sendCampaignEmail(selectedToken, campaignId, subject, body);
      setSendResult({ success: true, data: res });
    } catch (err) {
      setSendResult({ success: false, error: err.message });
    } finally {
      setSending(false);
    }
  };

  const handleSimulateBounce = async (e) => {
    e.preventDefault();
    setBouncing(true);
    setBounceResult(null);
    try {
      const res = await triggerBounceWebhook(bounceEmail);
      setBounceResult({ success: true, data: res });
    } catch (err) {
      setBounceResult({ success: false, error: err.message });
    } finally {
      setBouncing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold mb-2 border border-emerald-500/20">
          <Mail className="w-3.5 h-3.5" /> Phase 4: Privacy Gateway Blind Execution
        </div>
        <h2 className="text-xl font-bold text-white">Blind Operations & Provider Webhooks</h2>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Downstream applications trigger campaigns using protected tokens only. The Privacy Gateway decrypts inside an isolated boundary, sends via SMTP, and returns confirmation without ever exposing the real email address to the caller.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Campaign Sender */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
              <Send className="w-4 h-4 text-emerald-400" />
              1. Blind Marketing Campaign Sender
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              The marketing UI only selects an <span className="text-emerald-400 font-mono font-semibold">EMAIL_TOKEN</span>.
            </p>

            <form onSubmit={handleSendCampaign} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Select Recipient Token:</label>
                <select
                  value={selectedToken}
                  onChange={(e) => setSelectedToken(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs font-mono text-emerald-400 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                >
                  {customers.map((c) => (
                    <option key={c.customer_id} value={c.email_token}>
                      {c.customer_id} — {c.email_token} ({c.name_token})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-mono">Campaign ID:</label>
                  <input
                    type="text"
                    value={campaignId}
                    onChange={(e) => setCampaignId(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-mono">Subject:</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-mono">Email Body:</label>
                <textarea
                  rows={2}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2"
                />
              </div>

              <button
                type="submit"
                disabled={sending || !selectedToken}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs shadow-lg transition disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{sending ? 'Dispatching via Gateway...' : 'Send Campaign (Protected Token)'}</span>
              </button>
            </form>
          </div>

          {/* Response Payload */}
          {sendResult && (
            <div className="mt-4 p-3.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold mb-2">
                <CheckCircle className="w-4 h-4" />
                <span>Marketing Application API Response:</span>
              </div>
              <pre className="text-slate-300 bg-slate-950 p-2.5 rounded text-[11px] overflow-x-auto">
                {JSON.stringify(sendResult.data, null, 2)}
              </pre>
              <p className="text-[11px] text-emerald-400/90 mt-2">
                ✓ Zero plaintext leakage: Calling app receives only token confirmation.
              </p>
            </div>
          )}
        </div>

        {/* Provider Bounce Webhook Simulator */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
              <AlertOctagon className="w-4 h-4 text-amber-400" />
              2. Email Provider Bounce Webhook Handler
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Simulates a webhook from an external SMTP provider containing raw email. The gateway reverse-resolves it into a token before downstream storage.
            </p>

            <form onSubmit={handleSimulateBounce} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">External Webhook Raw Email:</label>
                <input
                  type="email"
                  value={bounceEmail}
                  onChange={(e) => setBounceEmail(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-red-400 font-mono rounded-lg px-3 py-2 focus:outline-none"
                  placeholder="e.g. john@example.com"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Bounce Event / Reason:</label>
                <input
                  type="text"
                  disabled
                  value="EVENT: BOUNCE | REASON: MAILBOX_NOT_FOUND"
                  className="w-full bg-slate-950 border border-slate-800 text-xs text-slate-500 font-mono rounded-lg px-3 py-2"
                />
              </div>

              <button
                type="submit"
                disabled={bouncing || !bounceEmail}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs shadow-lg transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${bouncing ? 'animate-spin' : ''}`} />
                <span>{bouncing ? 'Processing Webhook...' : 'Simulate Provider Bounce Callback'}</span>
              </button>
            </form>
          </div>

          {/* Bounce Output */}
          {bounceResult && (
            <div className="mt-4 p-3.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold mb-2">
                <CheckCircle className="w-4 h-4" />
                <span>Downstream Safe Ingestion Result:</span>
              </div>
              <pre className="text-slate-300 bg-slate-950 p-2.5 rounded text-[11px] overflow-x-auto">
                {JSON.stringify(bounceResult.data, null, 2)}
              </pre>
              <p className="text-[11px] text-amber-400/90 mt-2">
                ✓ Stored safely as token <span className="font-bold text-white">{bounceResult.data?.recipient}</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
