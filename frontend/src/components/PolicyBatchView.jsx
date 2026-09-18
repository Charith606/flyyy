import React, { useState, useEffect } from 'react';
import { Sliders, Play, CheckCircle, Clock, AlertTriangle, Layers, ArrowRight } from 'lucide-react';
import { fetchPolicies, updatePolicy, runBatchProtection, fetchBatches } from '../services/api';

export default function PolicyBatchView({ onProceedToProtected }) {
  const [policies, setPolicies] = useState([]);
  const [batches, setBatches] = useState([]);
  const [batchSize, setBatchSize] = useState(1000);
  const [loading, setLoading] = useState(false);
  const [lastRunResult, setLastRunResult] = useState(null);

  const loadData = async () => {
    try {
      const [polData, batchData] = await Promise.all([fetchPolicies(), fetchBatches()]);
      setPolicies(polData || []);
      setBatches(batchData || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePolicyChange = async (fieldName, newType) => {
    try {
      await updatePolicy(fieldName, newType);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunBatch = async () => {
    setLoading(true);
    try {
      const res = await runBatchProtection(batchSize);
      setLastRunResult(res);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Policy Configuration Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold mb-2 border border-blue-500/20">
              <Sliders className="w-3.5 h-3.5" /> Phase 2 & 3: Policy Store & Engine
            </div>
            <h2 className="text-xl font-bold text-white">Configurable Data Protection Policies</h2>
            <p className="text-slate-400 text-sm mt-1">
              Select which cryptographic transformation applies to each sensitive field during batch ingestion.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {policies.map((p) => (
            <div key={p.field_name} className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-white uppercase">{p.field_name}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                  {p.entity_type}
                </span>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1 font-medium">Protection Method:</label>
                <select
                  value={p.protection_type}
                  onChange={(e) => handlePolicyChange(p.field_name, e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 text-xs text-emerald-400 font-mono rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                >
                  <option value="FPE">FPE (Format-Preserving Encryption)</option>
                  <option value="TOKENIZATION">Deterministic Tokenization</option>
                  <option value="DYNAMIC_MASKING">Dynamic Masking</option>
                  <option value="KEEP_PLAINTEXT">Keep Plaintext (Non-PII)</option>
                </select>
              </div>

              <div className="text-[11px] text-slate-400">
                {p.protection_type === 'FPE' && 'Preserves 10-digit phone format reversibly.'}
                {p.protection_type === 'TOKENIZATION' && 'Outputs stable deterministic token e.g. EMAIL_XXXXX.'}
                {p.protection_type === 'KEEP_PLAINTEXT' && 'Attribute stored as-is without encryption.'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Batch Ingestion Runner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-400" />
              Batch Protection Pipeline Runner
            </h3>
            <p className="text-slate-400 text-xs mt-1">
              Executes chunked batch processing: reads source records, transforms fields with FPE/Tokens, loads protected database, and stores encrypted mappings in the isolated vault.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
              <label className="text-xs text-slate-400 font-mono">Chunk Size:</label>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="bg-slate-900 text-xs text-white rounded px-2 py-1 border border-slate-700 font-mono"
              >
                <option value={100}>100 rows</option>
                <option value={1000}>1,000 rows</option>
                <option value={10000}>10,000 rows</option>
              </select>
            </div>

            <button
              onClick={handleRunBatch}
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded-lg shadow-lg shadow-emerald-500/20 transition disabled:opacity-50 text-sm"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{loading ? 'Processing Batch...' : 'Trigger Batch Run'}</span>
            </button>
          </div>
        </div>

        {/* Last Run Banner */}
        {lastRunResult && (
          <div className="mt-4 p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <div className="text-xs">
                <span className="font-semibold text-emerald-300">Batch Completed: </span>
                <span className="font-mono text-white">{lastRunResult.batch_id}</span>
                <span className="text-slate-400 ml-2">
                  (Processed: {lastRunResult.row_count}, Success: {lastRunResult.success_count}, Errors: {lastRunResult.error_count})
                </span>
              </div>
            </div>

            <button
              onClick={onProceedToProtected}
              className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold hover:underline"
            >
              <span>View Protected Records</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Batch Runs History Table */}
        <div className="mt-6">
          <h4 className="text-xs font-semibold uppercase text-slate-400 font-mono mb-3">Recent Batch Executions</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3">Batch ID</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Rows Processed</th>
                  <th className="px-4 py-3">Success / Error</th>
                  <th className="px-4 py-3">Start Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {batches.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-6 text-center text-slate-500">
                      No batch runs recorded yet.
                    </td>
                  </tr>
                ) : (
                  batches.map((b) => (
                    <tr key={b.batch_id} className="hover:bg-slate-800/40">
                      <td className="px-4 py-3 font-semibold text-emerald-400">{b.batch_id}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 text-[10px]">
                          {b.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-white">{b.row_count}</td>
                      <td className="px-4 py-3">
                        <span className="text-emerald-400">{b.success_count}</span> /{' '}
                        <span className="text-red-400">{b.error_count}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{new Date(b.start_time).toLocaleTimeString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
