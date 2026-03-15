import React, { useState } from 'react';

const TwoFactorSetup: React.FC = () => {
  const [enabled, setEnabled] = useState(false);
  const [method, setMethod] = useState<'app' | 'sms' | 'email'>('app');
  const [qrCode, setQrCode] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [step, setStep] = useState(1);

  const setup2FA = async () => {
    // Generate QR code for TOTP app
    setQrCode('https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/CyberShield:admin?secret=JBSWY3DPEHPK3PXP&issuer=CyberShield');
    setStep(2);
  };

  const verifyCode = async () => {
    if (verificationCode.length === 6) {
      // Simulate verification
      alert('✅ 2FA enabled successfully!');
      setEnabled(true);
      setStep(3);
    }
  };

  const disable2FA = async () => {
    if (window.confirm('Are you sure you want to disable 2FA? This will make your account less secure.')) {
      setEnabled(false);
      setStep(1);
      setVerificationCode('');
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Two-Factor Authentication</h1>
        <p className="text-gray-600">Add an extra layer of security to your account</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        {!enabled ? (
          <>
            {step === 1 && (
              <>
                <div className="mb-6">
                  <h2 className="text-lg font-semibold mb-4">Choose Authentication Method</h2>
                  
                  <div className="space-y-3">
                    {[
                      { id: 'app', label: 'Authenticator App', icon: '📱', desc: 'Use Google Authenticator or Authy' },
                      { id: 'sms', label: 'SMS Authentication', icon: '💬', desc: 'Receive codes via text message' },
                      { id: 'email', label: 'Email Authentication', icon: '📧', desc: 'Receive codes via email' }
                    ].map((m) => (
                      <label
                        key={m.id}
                        className={`flex items-center p-4 border-2 rounded-lg cursor-pointer ${
                          method === m.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="method"
                          value={m.id}
                          checked={method === m.id}
                          onChange={(e) => setMethod(e.target.value as any)}
                          className="mr-3"
                        />
                        <span className="text-2xl mr-3">{m.icon}</span>
                        <div>
                          <div className="font-medium">{m.label}</div>
                          <div className="text-sm text-gray-600">{m.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={setup2FA}
                  className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                >
                  Set Up 2FA
                </button>
              </>
            )}

            {step === 2 && (
              <>
                <div className="mb-6">
                  <h2 className="text-lg font-semibold mb-4">Scan QR Code</h2>
                  
                  <div className="text-center">
                    <div className="inline-block p-4 bg-white border-2 rounded-lg mb-4">
                      <img src={qrCode} alt="2FA QR Code" className="mx-auto" />
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-4">
                      Scan this QR code with your authenticator app
                    </p>

                    <div className="bg-gray-50 p-3 rounded mb-4">
                      <div className="text-xs text-gray-600 mb-1">Manual entry code:</div>
                      <code className="text-sm font-mono">JBSWY3DPEHPK3PXP</code>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Verification Code</label>
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full border rounded px-4 py-2 text-center text-2xl tracking-widest"
                    placeholder="000000"
                    maxLength={6}
                  />
                </div>

                <button
                  onClick={verifyCode}
                  disabled={verificationCode.length !== 6}
                  className={`w-full py-3 rounded-lg font-medium ${
                    verificationCode.length === 6
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  Verify & Enable
                </button>
              </>
            )}
          </>
        ) : (
          <>
            <div className="text-center py-8">
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-xl font-bold text-green-600 mb-2">2FA is Enabled</h2>
              <p className="text-gray-600 mb-6">
                Your account is protected with two-factor authentication
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="font-medium text-blue-900 mb-2">Backup Codes</div>
                <div className="grid grid-cols-2 gap-2 text-sm font-mono">
                  <div>1234-5678</div>
                  <div>8765-4321</div>
                  <div>9999-0000</div>
                  <div>1111-2222</div>
                </div>
                <p className="text-xs text-blue-700 mt-2">
                  Save these codes in a safe place. You can use them to access your account if you lose your device.
                </p>
              </div>

              <button
                onClick={disable2FA}
                className="text-red-600 hover:text-red-800"
              >
                Disable 2FA
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TwoFactorSetup;
