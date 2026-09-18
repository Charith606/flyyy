import React, { useState, useEffect } from 'react';
import { Lock, Download, Eye, EyeOff, ShieldCheck, Check } from 'lucide-react';
import { fetchProtectedCustomers } from '../services/api';

export default function ProtectedDataView() {
  const [protectedData, setProtectedData] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [applyMasking, setApplyMasking] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadData = async (mask = applyMasking) => {
    setLoading(true);
    try {
      const res = await fetchProtectedCustomers(mask);
      setProtectedData(res.items || []);
      setTotalCount(res.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(applyMasking);
  }, [applyMasking]);

  const handleExportCsv = () => {
    window.open('/api/batch/export/csv', '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold mb-2 border border-emerald-500/20">
              <ShieldCheck className="w-3.5 h-3.5" /> Protected Customer Store (Downstream Data Source)
            </div>
            <h2 className="text-xl font-bold text-white">Zero-Plaintext Protected Database</h2>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              All downstream marketing, CRM, and analytics systems query this database. Notice phone numbers retain the exact 10-digit format (via FPE) while emails and names use tokens.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setApplyMasking(!applyMasking)}
              className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-lg border transition ${
                applyMasking
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
            >
              {applyMasking ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              <span>{applyMasking ? 'Dynamic Masking ON' : 'Dynamic Masking OFF'}</span>
            </button>

            <button
              onClick={handleExportCsv}
              className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow transition"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV (Protected)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Database Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white font-mono">
              TABLE: protected_customers ({totalCount} total records)
            </h3>
          </div>
          <span className="text-[11px] text-emerald-400 font-mono bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Plaintext PII: 0% (Isolated in Vault)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-700">
              <tr>
                <th className="px-4 py-3">Customer ID</th>
                <th className="px-4 py-3">Name Token</th>
                <th className="px-4 py-3">Email Token</th>
                <th className="px-4 py-3">Mobile (10-Digit FPE)</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3">Segment</th>
                <th className="px-4 py-3">Batch ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {protectedData.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-6 text-center text-slate-500">
                    No protected records yet. Go to "Policy & Batch" tab and click "Trigger Batch Run".
                  </td>
                </tr>
              ) : (
                protectedData.map((row) => (
                  <tr key={row.customer_id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-white">{row.customer_id}</td>
                    <td className="px-4 py-3 text-emerald-400 font-bold">{row.name_token}</td>
                    <td className="px-4 py-3 text-teal-300 font-bold">{row.email_token}</td>
                    <td className="px-4 py-3 text-sky-400 font-semibold">{row.mobile_fpe}</td>
                    <td className="px-4 py-3 text-slate-400">{row.city}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                        {row.segment}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-[10px]">{row.batch_id}</td>
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
