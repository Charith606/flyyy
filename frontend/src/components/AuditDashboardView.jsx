import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, ShieldAlert, Filter, RefreshCw, Lock } from 'lucide-react';
import { fetchAuditLogs } from '../services/api';

export default function AuditDashboardView() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [outcomeFilter, setOutcomeFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await fetchAuditLogs(outcomeFilter || null, actorFilter || null);
      setLogs(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [outcomeFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    loadLogs();
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold mb-2 border border-emerald-500/20">
              <Activity className="w-3.5 h-3.5" /> Phase 6: Immutable Compliance & Audit Trail
            </div>
            <h2 className="text-xl font-bold text-white">Central Security Audit Log</h2>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              Immutable, append-only security logs capturing all batch operations, blind campaigns, bounce webhooks, and reveal requests (both allowed and denied).
            </p>
          </div>

          <button
            onClick={loadLogs}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>

        {/* Filters */}
        <form onSubmit={handleSearch} className="mt-6 pt-4 border-t border-slate-800 flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-mono text-slate-400">Filter Outcome:</span>
            <select
              value={outcomeFilter}
              onChange={(e) => setOutcomeFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-2.5 py-1.5 font-mono"
            >
              <option value="">ALL OUTCOMES</option>
              <option value="ALLOWED">ALLOWED Only</option>
              <option value="ACCESS_DENIED">ACCESS_DENIED Only</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-slate-400">Actor:</span>
            <input
              type="text"
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
              placeholder="Search actor..."
              className="bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-2.5 py-1.5 font-mono"
            />
            <button
              type="submit"
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
            >
              Search
            </button>
          </div>

          <div className="ml-auto text-xs text-slate-400 font-mono">
            Total Audit Entries: <span className="text-white font-bold">{total}</span>
          </div>
        </form>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-700">
              <tr>
                <th className="px-3 py-3">Timestamp</th>
                <th className="px-3 py-3">Actor</th>
                <th className="px-3 py-3">Action</th>
                <th className="px-3 py-3">Subject ID / Token</th>
                <th className="px-3 py-3">Field</th>
                <th className="px-3 py-3">Purpose</th>
                <th className="px-3 py-3">Reference ID</th>
                <th className="px-3 py-3">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                    No audit records matching current criteria.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40">
                    <td className="px-3 py-3 text-slate-400 whitespace-nowrap">
                      {new Date(l.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-3 py-3 text-white font-semibold">{l.actor}</td>
                    <td className="px-3 py-3 text-cyan-300 font-medium">{l.action}</td>
                    <td className="px-3 py-3 text-emerald-400 font-bold">{l.subject_id || '—'}</td>
                    <td className="px-3 py-3 text-slate-300">{l.field || '—'}</td>
                    <td className="px-3 py-3 text-purple-300">{l.purpose || '—'}</td>
                    <td className="px-3 py-3 text-slate-400">{l.reference_id || '—'}</td>
                    <td className="px-3 py-3 whitespace-nowrap">
                      {l.outcome === 'ALLOWED' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/60 font-bold text-[10px]">
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          ALLOWED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-800/60 font-bold text-[10px]">
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                          ACCESS_DENIED
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
