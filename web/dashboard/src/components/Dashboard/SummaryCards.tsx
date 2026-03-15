import React from 'react';
import { DashboardSummary } from '../../types';

interface SummaryCardsProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary, loading }) => {
  if (loading) {
    return <div className="text-center py-10">Loading summary...</div>;
  }

  if (!summary) {
    return <div className="text-center py-10 text-red-500">Failed to load summary</div>;
  }

  const cards = [
    { label: 'Critical', value: summary.critical, color: 'bg-critical', icon: '🔴' },
    { label: 'High', value: summary.high, color: 'bg-high', icon: '🟠' },
    { label: 'Medium', value: summary.medium, color: 'bg-medium', icon: '🟡' },
    { label: 'Low', value: summary.low, color: 'bg-low', icon: '🔵' },
    { label: 'Info', value: summary.info, color: 'bg-info', icon: '⚪' },
  ];

  return (
    <div className="grid grid-cols-5 gap-4 mb-8">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`${card.color} text-white rounded-lg shadow-lg p-6`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">{card.label}</p>
              <p className="text-4xl font-bold mt-2">{card.value}</p>
            </div>
            <div className="text-4xl">{card.icon}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;
