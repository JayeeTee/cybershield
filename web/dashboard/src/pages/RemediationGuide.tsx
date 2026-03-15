import React, { useState } from 'react';

interface Remediation {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  description: string;
  steps: string[];
  references: { title: string; url: string }[];
  automated: boolean;
}

const RemediationGuide: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const remediations: Remediation[] = [
    {
      id: '1',
      title: 'S3 Bucket Public Access',
      severity: 'critical',
      category: 'Cloud Security',
      description: 'S3 bucket is configured to allow public read/write access, potentially exposing sensitive data.',
      steps: [
        'Navigate to AWS S3 Console',
        'Select the affected bucket',
        'Go to Permissions tab',
        'Click "Block public access"',
        'Enable all four block settings',
        'Review bucket policy and ACL',
        'Remove any public grants',
        'Enable bucket encryption',
        'Enable versioning for recovery'
      ],
      references: [
        { title: 'AWS S3 Security Best Practices', url: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html' },
        { title: 'CIS AWS Benchmark', url: 'https://www.cisecurity.org/benchmark/amazon_web_services' }
      ],
      automated: true
    },
    {
      id: '2',
      title: 'Outdated TLS Version',
      severity: 'high',
      category: 'Network Security',
      description: 'Server is using outdated TLS 1.0/1.1 which has known vulnerabilities.',
      steps: [
        'Identify affected services',
        'Update server configuration',
        'Disable TLS 1.0 and 1.1',
        'Enable TLS 1.2 and 1.3',
        'Update cipher suites',
        'Test with SSL Labs',
        'Update client applications if needed',
        'Monitor for connection errors'
      ],
      references: [
        { title: 'NIST TLS Guidelines', url: 'https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final' },
        { title: 'SSL Labs Best Practices', url: 'https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices' }
      ],
      automated: false
    },
    {
      id: '3',
      title: 'Exposed API Keys in Repository',
      severity: 'critical',
      category: 'Secrets Management',
      description: 'API keys or credentials detected in source code repository.',
      steps: [
        'Immediately rotate the exposed credential',
        'Remove the key from git history using BFG or git-filter-repo',
        'Add the file to .gitignore',
        'Use environment variables or secrets manager',
        'Scan repository for other secrets',
        'Enable pre-commit hooks to prevent future leaks',
        'Review access logs for unauthorized usage',
        'Notify security team'
      ],
      references: [
        { title: 'OWASP Secret Management', url: 'https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html' },
        { title: 'Git Secrets Tool', url: 'https://github.com/awslabs/git-secrets' }
      ],
      automated: true
    },
    {
      id: '4',
      title: 'Container Image Vulnerabilities',
      severity: 'high',
      category: 'Container Security',
      description: 'Docker image contains packages with known CVEs.',
      steps: [
        'Run vulnerability scanner (Trivy, Clair, etc.)',
        'Update base image to latest version',
        'Update affected packages',
        'Rebuild container image',
        'Scan updated image',
        'Test application functionality',
        'Deploy to staging',
        'Monitor for issues',
        'Deploy to production'
      ],
      references: [
        { title: 'Docker Security Best Practices', url: 'https://docs.docker.com/develop/security-best-practices/' },
        { title: 'CIS Docker Benchmark', url: 'https://www.cisecurity.org/benchmark/docker' }
      ],
      automated: true
    }
  ];

  const categories = ['all', ...Array.from(new Set(remediations.map(r => r.category)))];

  const filteredRemediations = remediations.filter(rem => {
    const matchesCategory = selectedCategory === 'all' || rem.category === selectedCategory;
    const matchesSearch = rem.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          rem.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-500';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-500';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-500';
      default: return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Remediation Guide</h1>
        <p className="text-gray-600">Step-by-step instructions for fixing security vulnerabilities</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Search remediations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 border rounded px-4 py-2"
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border rounded px-4 py-2"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Remediation Cards */}
      <div className="space-y-4">
        {filteredRemediations.map((remediation) => (
          <details key={remediation.id} className="bg-white rounded-lg shadow overflow-hidden">
            <summary className="p-6 cursor-pointer hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded text-sm font-semibold border-l-4 ${getSeverityColor(remediation.severity)}`}>
                    {remediation.severity.toUpperCase()}
                  </span>
                  <div>
                    <div className="font-semibold text-lg">{remediation.title}</div>
                    <div className="text-sm text-gray-600">{remediation.category}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {remediation.automated && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                      ⚡ Auto-fix available
                    </span>
                  )}
                  <span className="text-gray-400 text-sm">Click to expand</span>
                </div>
              </div>
            </summary>
            
            <div className="p-6 border-t bg-gray-50">
              <p className="text-gray-700 mb-4">{remediation.description}</p>
              
              <div className="mb-4">
                <h3 className="font-semibold mb-2">📋 Remediation Steps:</h3>
                <ol className="list-decimal list-inside space-y-2">
                  {remediation.steps.map((step, idx) => (
                    <li key={idx} className="text-gray-700">
                      {step}
                    </li>
                  ))}
                </ol>
              </div>

              {remediation.references.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">📚 References:</h3>
                  <div className="flex flex-wrap gap-2">
                    {remediation.references.map((ref, idx) => (
                      <a
                        key={idx}
                        href={ref.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm"
                      >
                        🔗 {ref.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {remediation.automated && (
                <div className="mt-4 pt-4 border-t">
                  <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                    ⚡ Apply Automated Fix
                  </button>
                </div>
              )}
            </div>
          </details>
        ))}
      </div>

      {filteredRemediations.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No remediations found matching your criteria
        </div>
      )}
    </div>
  );
};

export default RemediationGuide;
