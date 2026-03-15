import React, { useState, useEffect } from 'react';

interface Schedule {
  id: string;
  name: string;
  scanner_type: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string;
  day_of_week?: number;
  day_of_month?: number;
  enabled: boolean;
  last_run?: string;
  next_run: string;
}

const ScheduledScans: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([
    {
      id: '1',
      name: 'Weekly Cloud Security Scan',
      scanner_type: 'cloud_security',
      frequency: 'weekly',
      time: '02:00',
      day_of_week: 1,
      enabled: true,
      next_run: '2026-03-09T02:00:00Z'
    },
    {
      id: '2',
      name: 'Daily Container Scan',
      scanner_type: 'container',
      frequency: 'daily',
      time: '06:00',
      enabled: true,
      last_run: '2026-03-02T06:00:00Z',
      next_run: '2026-03-03T06:00:00Z'
    }
  ]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    name: '',
    scanner_type: 'cloud_security',
    frequency: 'weekly' as Schedule['frequency'],
    time: '02:00',
    day_of_week: 1,
    day_of_month: 1
  });

  const scannerTypes = [
    { id: 'cloud_security', label: 'Cloud Security', icon: '☁️' },
    { id: 'secrets_detection', label: 'Secrets Detection', icon: '🔐' },
    { id: 'container', label: 'Container Scanner', icon: '🐳' },
    { id: 'network', label: 'Network Analysis', icon: '🌐' },
    { id: 'threat_intel', label: 'Threat Intelligence', icon: '🕵️' }
  ];

  const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const createSchedule = () => {
    const schedule: Schedule = {
      id: Date.now().toString(),
      ...newSchedule,
      enabled: true,
      next_run: new Date(Date.now() + 86400000).toISOString()
    };
    setSchedules([...schedules, schedule]);
    setShowCreateModal(false);
    setNewSchedule({
      name: '',
      scanner_type: 'cloud_security',
      frequency: 'weekly',
      time: '02:00',
      day_of_week: 1,
      day_of_month: 1
    });
  };

  const toggleSchedule = (id: string) => {
    setSchedules(schedules.map(s => 
      s.id === id ? { ...s, enabled: !s.enabled } : s
    ));
  };

  const deleteSchedule = (id: string) => {
    if (window.confirm('Delete this scheduled scan?')) {
      setSchedules(schedules.filter(s => s.id !== id));
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFrequencyLabel = (schedule: Schedule) => {
    switch (schedule.frequency) {
      case 'daily': return `Daily at ${schedule.time}`;
      case 'weekly': return `Every ${daysOfWeek[schedule.day_of_week!]} at ${schedule.time}`;
      case 'monthly': return `Monthly on day ${schedule.day_of_month} at ${schedule.time}`;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scheduled Scans</h1>
          <p className="text-gray-600">Automate your security scans</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ➕ Create Schedule
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Total Schedules</div>
          <div className="text-3xl font-bold">{schedules.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Active</div>
          <div className="text-3xl font-bold text-green-600">
            {schedules.filter(s => s.enabled).length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Paused</div>
          <div className="text-3xl font-bold text-gray-400">
            {schedules.filter(s => !s.enabled).length}
          </div>
        </div>
      </div>

      {/* Schedules List */}
      <div className="bg-white rounded-lg shadow">
        {schedules.map((schedule) => (
          <div key={schedule.id} className="border-b p-6 last:border-b-0">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <span className="text-3xl">
                  {scannerTypes.find(s => s.id === schedule.scanner_type)?.icon}
                </span>
                <div>
                  <div className="font-semibold text-lg">{schedule.name}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {getFrequencyLabel(schedule)}
                  </div>
                  <div className="flex gap-4 mt-2">
                    {schedule.last_run && (
                      <span className="text-sm text-gray-500">
                        Last run: {formatDate(schedule.last_run)}
                      </span>
                    )}
                    <span className="text-sm text-blue-600">
                      Next run: {formatDate(schedule.next_run)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={schedule.enabled}
                    onChange={() => toggleSchedule(schedule.id)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                </label>
                <button
                  onClick={() => deleteSchedule(schedule.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        ))}

        {schedules.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No scheduled scans yet. Create one to automate your security scans!
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowCreateModal(false)} />
          <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full m-4 max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold">Create Scheduled Scan</h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Schedule Name</label>
                  <input
                    type="text"
                    value={newSchedule.name}
                    onChange={(e) => setNewSchedule({ ...newSchedule, name: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                    placeholder="e.g., Weekly Cloud Scan"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Scanner Type</label>
                  <select
                    value={newSchedule.scanner_type}
                    onChange={(e) => setNewSchedule({ ...newSchedule, scanner_type: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                  >
                    {scannerTypes.map(type => (
                      <option key={type.id} value={type.id}>
                        {type.icon} {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Frequency</label>
                  <select
                    value={newSchedule.frequency}
                    onChange={(e) => setNewSchedule({ ...newSchedule, frequency: e.target.value as any })}
                    className="w-full border rounded px-4 py-2"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Time</label>
                  <input
                    type="time"
                    value={newSchedule.time}
                    onChange={(e) => setNewSchedule({ ...newSchedule, time: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                  />
                </div>

                {newSchedule.frequency === 'weekly' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Day of Week</label>
                    <select
                      value={newSchedule.day_of_week}
                      onChange={(e) => setNewSchedule({ ...newSchedule, day_of_week: parseInt(e.target.value) })}
                      className="w-full border rounded px-4 py-2"
                    >
                      {daysOfWeek.map((day, idx) => (
                        <option key={idx} value={idx}>{day}</option>
                      ))}
                    </select>
                  </div>
                )}

                {newSchedule.frequency === 'monthly' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Day of Month</label>
                    <select
                      value={newSchedule.day_of_month}
                      onChange={(e) => setNewSchedule({ ...newSchedule, day_of_month: parseInt(e.target.value) })}
                      className="w-full border rounded px-4 py-2"
                    >
                      {Array.from({ length: 28 }, (_, i) => i + 1).map(day => (
                        <option key={day} value={day}>{day}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-lg">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  onClick={createSchedule}
                  disabled={!newSchedule.name}
                  className={`px-4 py-2 rounded text-white ${
                    newSchedule.name ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'
                  }`}
                >
                  Create Schedule
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ScheduledScans;
