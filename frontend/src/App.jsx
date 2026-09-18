import React, { useState } from 'react';
import Navbar from './components/Navbar';
import DiscoveryView from './components/DiscoveryView';
import PolicyBatchView from './components/PolicyBatchView';
import ProtectedDataView from './components/ProtectedDataView';
import MarketingGatewayDemo from './components/MarketingGatewayDemo';
import ControlledRevealDemo from './components/ControlledRevealDemo';
import AuditDashboardView from './components/AuditDashboardView';
import { seedSourceData } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('discovery');
  const [notification, setNotification] = useState(null);

  const showNotification = (msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  const handleSeedData = async () => {
    try {
      await seedSourceData(50);
      showNotification('Successfully seeded 50 customer records into source database!');
      // reload or trigger tab refresh
      window.location.reload();
    } catch (err) {
      showNotification('Failed to seed data: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSeed={handleSeedData}
      />

      {/* Global Notification Toast */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-emerald-600 text-white text-xs font-semibold px-4 py-3 rounded-xl shadow-2xl border border-emerald-400/40 animate-bounce">
          {notification}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'discovery' && (
          <DiscoveryView onProceedToBatch={() => setActiveTab('batch')} />
        )}

        {activeTab === 'batch' && (
          <PolicyBatchView onProceedToProtected={() => setActiveTab('protected')} />
        )}

        {activeTab === 'protected' && (
          <ProtectedDataView />
        )}

        {activeTab === 'marketing' && (
          <MarketingGatewayDemo />
        )}

        {activeTab === 'reveal' && (
          <ControlledRevealDemo onProceedToAudit={() => setActiveTab('audit')} />
        )}

        {activeTab === 'audit' && (
          <AuditDashboardView />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        Flyyy.ai Privacy-Preserving Customer Data Platform • Format-Preserving Encryption & Vault Architecture
      </footer>
    </div>
  );
}
