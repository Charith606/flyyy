import React, { useState, useEffect } from 'react';
import { Search, Sparkles, CheckCircle2, AlertCircle, Database, ShieldAlert, ArrowRight } from 'lucide-react';
import { fetchSourceCustomers, runDiscovery } from '../services/api';

export default function DiscoveryView({ onProceedToBatch }) {
  const [sourceData, setSourceData] = useState([]);
  const [discoveryResults, setDiscoveryResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const res = await fetchSourceCustomers(10);
      setSourceData(res.items || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunDiscovery = async () => {
    setLoading(true);
    try {
      const res = await runDiscovery();
      setDiscoveryResults(res.fields || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold mb-2 border border-emerald-500/20">
              <Sparkles className="w-3.5 h-3.5" /> Phase 1: Automated PII Discovery
            </div>
            <h2 className="text-xl font-bold text-white">Source Data & PII Classification Engine</h2>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              Inspects ingested raw customer tables, applies Presidio & Regex entity classifiers, and computes confidence scores to suggest protection strategies.
            </p>
          </div>
          <button
            onClick={handleRunDiscovery}
            disabled={loading}
            className="flex items-center justify-center space-x-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded-lg shadow-lg shadow-emerald-500/20 transition disabled:opacity-50 text-sm"
          >
            <Search className="w-4 h-4" />
            <span>{loading ? 'Analyzing Source...' : 'Run PII Discovery'}</span>
          </button>
        </div>
      </div>

      {/* Discovery Results Cards */}
      {discoveryResults && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Automated PII Discovery Report
            </h3>
            <span className="text-xs text-slate-400">Classified {discoveryResults.length} fields</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {discoveryResults.map((f) => {
              const isPii = f.confidence >= 0.7;
              return (
                <div
                  key={f.field_name}
                  className={`p-4 rounded-xl border transition ${
                    isPii
                      ? 'bg-amber-950/20 border-amber-800/40 text-amber-200'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-semibold text-white">{f.field_name}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        isPii ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {f.entity_type}
                    </span>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Confidence Score:</span>
                    <span className="font-mono font-bold text-white">{(f.confidence * 100).toFixed(0)}%</span>
                  </div>

                  <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full ${isPii ? 'bg-amber-500' : 'bg-slate-600'}`}
                      style={{ width: `${Math.max(f.confidence * 100, 10)}%` }}
                    />
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Recommended Action:</span>
                    <span className="font-mono font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                      {f.recommended_action}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onProceedToBatch}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 text-xs font-semibold rounded-lg transition"
            >
              <span>Proceed to Policy & Batch Protection</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Raw Source Data Preview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-slate-400" />
              Source Database Preview (Read-Only Raw Records)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Contains unencrypted PII before batch protection. Downstream applications will NEVER have access to this store.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-700">
              <tr>
                <th className="px-4 py-3">Customer ID</th>
                <th className="px-4 py-3">Full Name</th>
                <th className="px-4 py-3">Email Address (PII)</th>
                <th className="px-4 py-3">Mobile (PII)</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3">Segment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {sourceData.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-6 text-center text-slate-500">
                    No source records found. Click "Reset & Seed Data" at the top right to populate.
                  </td>
                </tr>
              ) : (
                sourceData.map((row) => (
                  <tr key={row.customer_id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-white">{row.customer_id}</td>
                    <td className="px-4 py-3 text-slate-200">{row.name}</td>
                    <td className="px-4 py-3 text-red-400/90">{row.email}</td>
                    <td className="px-4 py-3 text-amber-400/90">{row.mobile}</td>
                    <td className="px-4 py-3 text-slate-400">{row.city}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                        {row.segment}
                      </span>
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
