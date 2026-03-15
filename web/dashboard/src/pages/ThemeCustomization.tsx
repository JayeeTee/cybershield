import React, { useState } from 'react';

const ThemeCustomization: React.FC = () => {
  const [theme, setTheme] = useState({
    mode: 'light' as 'light' | 'dark',
    primaryColor: 'blue',
    fontFamily: 'inter',
    fontSize: 'medium',
    sidebarStyle: 'expanded' as 'expanded' | 'compact' | 'icons-only',
    dashboardLayout: 'cards' as 'cards' | 'table' | 'compact',
    customCSS: ''
  });

  const colorOptions = [
    { id: 'blue', label: 'Blue', color: '#3B82F6' },
    { id: 'purple', label: 'Purple', color: '#8B5CF6' },
    { id: 'green', label: 'Green', color: '#10B981' },
    { id: 'red', label: 'Red', color: '#EF4444' },
    { id: 'orange', label: 'Orange', color: '#F97316' },
    { id: 'pink', label: 'Pink', color: '#EC4899' }
  ];

  const fontOptions = [
    { id: 'inter', label: 'Inter' },
    { id: 'roboto', label: 'Roboto' },
    { id: 'opensans', label: 'Open Sans' },
    { id: 'montserrat', label: 'Montserrat' }
  ];

  const sizeOptions = [
    { id: 'small', label: 'Small' },
    { id: 'medium', label: 'Medium' },
    { id: 'large', label: 'Large' }
  ];

  const applyTheme = () => {
    alert('✅ Theme settings applied!');
  };

  const resetTheme = () => {
    if (window.confirm('Reset to default theme?')) {
      setTheme({
        mode: 'light',
        primaryColor: 'blue',
        fontFamily: 'inter',
        fontSize: 'medium',
        sidebarStyle: 'expanded',
        dashboardLayout: 'cards',
        customCSS: ''
      });
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Theme & Customization</h1>
        <p className="text-gray-600">Personalize your CyberShield experience</p>
      </div>

      {/* Light/Dark Mode */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">🌓 Color Mode</h2>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setTheme({ ...theme, mode: 'light' })}
            className={`p-6 border-2 rounded-lg ${
              theme.mode === 'light' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-4xl mb-2">☀️</div>
            <div className="font-medium">Light Mode</div>
          </button>
          <button
            onClick={() => setTheme({ ...theme, mode: 'dark' })}
            className={`p-6 border-2 rounded-lg ${
              theme.mode === 'dark' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-4xl mb-2">🌙</div>
            <div className="font-medium">Dark Mode</div>
          </button>
        </div>
      </div>

      {/* Primary Color */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">🎨 Primary Color</h2>
        <div className="grid grid-cols-6 gap-3">
          {colorOptions.map((color) => (
            <button
              key={color.id}
              onClick={() => setTheme({ ...theme, primaryColor: color.id })}
              className={`p-4 border-2 rounded-lg ${
                theme.primaryColor === color.id ? 'border-gray-800 ring-2 ring-offset-2 ring-gray-400' : 'border-gray-200'
              }`}
            >
              <div
                className="w-full h-8 rounded mb-2"
                style={{ backgroundColor: color.color }}
              />
              <div className="text-xs font-medium">{color.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Typography */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">✍️ Typography</h2>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Font Family</label>
            <select
              value={theme.fontFamily}
              onChange={(e) => setTheme({ ...theme, fontFamily: e.target.value })}
              className="w-full border rounded px-4 py-2"
            >
              {fontOptions.map(font => (
                <option key={font.id} value={font.id}>{font.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Font Size</label>
            <select
              value={theme.fontSize}
              onChange={(e) => setTheme({ ...theme, fontSize: e.target.value })}
              className="w-full border rounded px-4 py-2"
            >
              {sizeOptions.map(size => (
                <option key={size.id} value={size.id}>{size.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded">
          <div className="text-sm text-gray-600 mb-2">Preview:</div>
          <div style={{ fontFamily: theme.fontFamily }}>
            <div className="text-3xl font-bold mb-2">CyberShield Security</div>
            <div className="text-lg mb-2">Your comprehensive security platform</div>
            <div className="text-base">Scan results show 45 findings across 5 scanners.</div>
          </div>
        </div>
      </div>

      {/* Layout Options */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">📐 Layout Options</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Sidebar Style</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'expanded', label: 'Expanded', icon: '◀▶' },
                { id: 'compact', label: 'Compact', icon: '◀▶' },
                { id: 'icons-only', label: 'Icons Only', icon: '•••' }
              ].map(style => (
                <button
                  key={style.id}
                  onClick={() => setTheme({ ...theme, sidebarStyle: style.id as any })}
                  className={`p-3 border-2 rounded ${
                    theme.sidebarStyle === style.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="text-2xl mb-1">{style.icon}</div>
                  <div className="text-sm">{style.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Dashboard Layout</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'cards', label: 'Cards', icon: '▦' },
                { id: 'table', label: 'Table', icon: '☰' },
                { id: 'compact', label: 'Compact', icon: '▬' }
              ].map(layout => (
                <button
                  key={layout.id}
                  onClick={() => setTheme({ ...theme, dashboardLayout: layout.id as any })}
                  className={`p-3 border-2 rounded ${
                    theme.dashboardLayout === layout.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="text-2xl mb-1">{layout.icon}</div>
                  <div className="text-sm">{layout.label}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Custom CSS */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">💅 Custom CSS</h2>
        <textarea
          value={theme.customCSS}
          onChange={(e) => setTheme({ ...theme, customCSS: e.target.value })}
          className="w-full border rounded px-4 py-3 font-mono text-sm"
          rows={6}
          placeholder="/* Add custom CSS styles here */"
        />
        <p className="text-xs text-gray-500 mt-2">
          Advanced: Add custom CSS to override default styles
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={applyTheme}
          className="px-6 py-3 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
        >
          Apply Theme
        </button>
        <button
          onClick={resetTheme}
          className="px-6 py-3 border rounded font-medium hover:bg-gray-50"
        >
          Reset to Default
        </button>
      </div>

      {/* Live Preview */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">👁️ Live Preview</h2>
        <div className={`p-6 rounded-lg border ${theme.mode === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-50'}`}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white`}
                 style={{ backgroundColor: colorOptions.find(c => c.id === theme.primaryColor)?.color }}>
              🛡️
            </div>
            <div>
              <div className="font-bold text-xl">CyberShield</div>
              <div className="text-sm opacity-75">Security Dashboard</div>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-3">
            <div className="p-4 bg-white bg-opacity-10 rounded">
              <div className="text-2xl font-bold">45</div>
              <div className="text-xs opacity-75">Total Findings</div>
            </div>
            <div className="p-4 bg-white bg-opacity-10 rounded">
              <div className="text-2xl font-bold">12</div>
              <div className="text-xs opacity-75">Critical</div>
            </div>
            <div className="p-4 bg-white bg-opacity-10 rounded">
              <div className="text-2xl font-bold">67%</div>
              <div className="text-xs opacity-75">Remediated</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeCustomization;
