import React, { useState, useEffect } from 'react';
import { Eye, ShieldAlert, CheckCircle, XCircle, Key, Lock, ArrowRight } from 'lucide-react';
import { fetchProtectedCustomers, requestControlledReveal } from '../services/api';

export default function ControlledRevealDemo({ onProceedToAudit }) {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState('C001');
  const [field, setField] = useState('EMAIL');
  const [purpose, setPurpose] = useState('CUSTOMER_SUPPORT');
  const [reference, setReference] = useState('TICKET-1091');
  const [actor, setActor] = useState('support_agent_sarah');
  const [loading, setLoading] = useState(false);
  const [revealResult, setRevealResult] = useState(null);

  useEffect(() => {
    fetchProtectedCustomers(false).then((res) => {
      const items = res.items || [];
      setCustomers(items);
      if (items.length > 0) {
        setSelectedCustomerId(items[0].customer_id);
      }
    });
  }, []);

  const handleReveal = async (e) => {
    e.preventDefault();
    setLoading(true);
    setRevealResult(null);
    try {
      const res = await requestControlledReveal(selectedCustomerId, field, purpose, reference, actor);
      setRevealResult({ success: true, data: res });
    } catch (err) {
      setRevealResult({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const setDemoScenario = (scenario) => {
    if (scenario === 'authorized') {
      setActor('support_agent_sarah');
      setPurpose('CUSTOMER_SUPPORT');
      setReference('TICKET-1091');
      setField('EMAIL');
    } else if (scenario === 'unauthorized_role') {
      setActor('unauthorized_guest');
      setPurpose('CUSTOMER_SUPPORT');
      setReference('TICKET-1091');
    } else if (scenario === 'unauthorized_purpose') {
      setActor('support_agent_sarah');
      setPurpose('GENERIC_BROWSING');
      setReference('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-400 text-xs font-semibold mb-2 border border-purple-500/20">
          <Eye className="w-3.5 h-3.5" /> Phase 5: Controlled Reveal Exception Portal
        </div>
        <h2 className="text-xl font-bold text-white">Role & Purpose-Based Plaintext Reveal</h2>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Plaintext PII is accessible strictly as a controlled exception. The Privacy Gateway authenticates the user, verifies legitimate business purpose + ticket reference, retrieves the key from the vault, and writes an immutable audit record.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Panel */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase font-mono flex items-center gap-2">
              <Key className="w-4 h-4 text-purple-400" />
              Controlled Reveal Request Form
            </h3>

            {/* Quick Scenario Buttons */}
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setDemoScenario('authorized')}
                className="px-2 py-1 text-[11px] rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60 hover:bg-emerald-900"
              >
                Preset: Authorized Support
              </button>
              <button
                type="button"
                onClick={() => setDemoScenario('unauthorized_role')}
                className="px-2 py-1 text-[11px] rounded bg-red-950 text-red-300 border border-red-800/60 hover:bg-red-900"
              >
                Preset: Unauthorized Role
              </button>
              <button
                type="button"
                onClick={() => setDemoScenario('unauthorized_purpose')}
                className="px-2 py-1 text-[11px] rounded bg-amber-950 text-amber-300 border border-amber-800/60 hover:bg-amber-900"
              >
                Preset: Generic Browsing
              </button>
            </div>
          </div>

          <form onSubmit={handleReveal} className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Target Customer ID:</label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs font-mono text-white rounded-lg px-3 py-2"
                >
                  {customers.map((c) => (
                    <option key={c.customer_id} value={c.customer_id}>
                      {c.customer_id} ({c.name_token})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Field to Reveal:</label>
                <select
                  value={field}
                  onChange={(e) => setField(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs font-mono text-white rounded-lg px-3 py-2"
                >
                  <option value="EMAIL">EMAIL (Tokenized)</option>
                  <option value="MOBILE">MOBILE (FPE Encrypted)</option>
                  <option value="NAME">NAME (Tokenized)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Actor / Requesting Role:</label>
                <input
                  type="text"
                  value={actor}
                  onChange={(e) => setActor(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 font-mono"
                  placeholder="e.g. support_agent_sarah"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Declared Business Purpose:</label>
                <select
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs font-mono text-white rounded-lg px-3 py-2"
                >
                  <option value="CUSTOMER_SUPPORT">CUSTOMER_SUPPORT (Authorized)</option>
                  <option value="FRAUD_INVESTIGATION">FRAUD_INVESTIGATION (Authorized)</option>
                  <option value="LEGAL_COMPLIANCE">LEGAL_COMPLIANCE (Authorized)</option>
                  <option value="GENERIC_BROWSING">GENERIC_BROWSING (Unauthorized)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1">
                Audit Ticket Reference (Mandatory):
              </label>
              <input
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 font-mono"
                placeholder="e.g. TICKET-1091 or CASE-5432"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg text-xs shadow-lg transition disabled:opacity-50"
            >
              <Eye className="w-4 h-4" />
              <span>{loading ? 'Evaluating Access Policy...' : 'Submit Controlled Reveal Request'}</span>
            </button>
          </form>
        </div>

        {/* Verification / Result Panel */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase font-mono mb-3">Gateway Access Decision</h3>

            {!revealResult && (
              <div className="h-48 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                <Lock className="w-8 h-8 text-slate-600 mb-2" />
                Submit a request on the left to evaluate Gateway access policies and audit controls.
              </div>
            )}

            {revealResult && revealResult.success && (
              <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 space-y-3">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <CheckCircle className="w-5 h-5" />
                  <span>ACCESS_GRANTED (Status: 200 OK)</span>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1 text-xs font-mono">
                  <div className="text-slate-400">Decrypted Plaintext Value:</div>
                  <div className="text-emerald-300 text-sm font-bold select-all bg-emerald-950/80 px-2 py-1 rounded border border-emerald-800/50">
                    {revealResult.data.plaintext_value}
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 space-y-0.5">
                  <div>Subject: <span className="text-white font-mono">{revealResult.data.subject_id}</span></div>
                  <div>Purpose: <span className="text-white font-mono">{revealResult.data.purpose}</span></div>
                  <div>Reference: <span className="text-white font-mono">{revealResult.data.reference}</span></div>
                </div>
              </div>
            )}

            {revealResult && !revealResult.success && (
              <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 space-y-3">
                <div className="flex items-center gap-2 text-red-400 font-bold text-xs">
                  <XCircle className="w-5 h-5" />
                  <span>ACCESS_DENIED (Status: 403 Forbidden)</span>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-red-300">
                  {revealResult.error}
                </div>

                <p className="text-[11px] text-slate-400">
                  Denial logged immediately into the immutable audit database with actor, IP, timestamp, and justification failure.
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
            <button
              onClick={onProceedToAudit}
              className="flex items-center gap-1.5 text-xs text-purple-400 font-semibold hover:underline"
            >
              <span>Inspect Audit Trail for this Event</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
