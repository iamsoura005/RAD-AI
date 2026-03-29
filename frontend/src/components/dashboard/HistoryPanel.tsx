import { History, FileImage, FileText, Clock } from 'lucide-react';
import { useState } from 'react';

interface HistoryItem {
  id: number;
  name: string;
  date: string;
  type: 'image' | 'csv';
  risk: string;
  modality: string;
}

const INITIAL_HISTORY: HistoryItem[] = [
  { id: 2, name: 'chest_xray_764.png', date: 'Yesterday', type: 'image', risk: 'Medium', modality: 'Chest X-Ray' },
  { id: 3, name: 'brain_mri_flair.jpg', date: 'Oct 14', type: 'image', risk: 'High', modality: 'Brain MRI' },
  { id: 4, name: 'ecg_signal.csv', date: 'Oct 12', type: 'csv', risk: 'Low', modality: 'Signal' },
];

interface Props {
  currentFile: string;
  modality: string;
  risk: string;
}

const riskDot = (risk: string) =>
  risk === 'High' ? 'bg-danger' : risk === 'Medium' ? 'bg-warning' : risk === 'Low' ? 'bg-success' : 'bg-gray-500';

export default function HistoryPanel({ currentFile, modality, risk }: Props) {
  const [history] = useState<HistoryItem[]>([
    { id: 1, name: currentFile, date: 'Just now', type: 'image', risk, modality: modality.replace('_', ' ') },
    ...INITIAL_HISTORY,
  ]);

  return (
    <div className="glass-card flex flex-col h-full w-full">
      <div className="p-4 border-b border-cardBorder flex items-center gap-2">
        <History size={18} className="text-gray-400" />
        <h3 className="font-semibold text-sm">Scan History</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {history.map((item, index) => (
          <div
            key={item.id}
            className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors group ${
              index === 0 ? 'bg-primary/10 border border-primary/20' : 'hover:bg-white/5'
            }`}
          >
            <div className={`p-2 rounded-md flex-shrink-0 ${
              item.type === 'image' ? 'bg-primary/20 text-primary' : 'bg-accent/20 text-accent'
            }`}>
              {item.type === 'image' ? <FileImage size={16} /> : <FileText size={16} />}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate group-hover:text-primary transition-colors">
                {item.name}
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Clock size={10} className="text-gray-600" />
                <p className="text-xs text-gray-500">{item.date}</p>
                <span className="text-gray-600">·</span>
                <p className="text-xs text-gray-500">{item.modality}</p>
              </div>
            </div>

            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${riskDot(item.risk)}`} title={`${item.risk} Risk`} />
          </div>
        ))}
      </div>

      <div className="p-4">
        <button className="w-full py-2 text-sm text-center border border-cardBorder rounded-lg hover:bg-cardBorder transition-colors text-gray-400">
          View All History
        </button>
      </div>
    </div>
  );
}
