/**
 * SetupWizard Component
 * 
 * Embedded React component for Shopify app setup wizard
 * Step-by-step setup flow after customer installs NeuroCommerce from Shopify App Store
 * 
 * Steps:
 * 1. Account Setup - Create account & link Shopify store
 * 2. Store Configuration - Basic store info & settings  
 * 3. Agent Setup - Select & enable AI agents
 * 4. Completion - Activate and deploy
 */

import React, { useState, useEffect } from 'react';
import './SetupWizard.css';

interface SetupStep {
  step: number;
  title: string;
  description: string;
  completed: boolean;
}

interface Store {
  storeId: string;
  shopDomain: string;
  accessToken: string;
}

export const SetupWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [store, setStore] = useState<Store | null>(null);
  const [completed, setCompleted] = useState(false);

  // Step 0: OAuth (happens before wizard in setup.py)
  // Step 1: Account Setup
  const [accountForm, setAccountForm] = useState({
    owner_email: '',
    password: '',
    confirm_password: '',
    owner_first_name: '',
    owner_last_name: '',
    shop_name: ''
  });

  // Step 2: Store Configuration
  const [storeConfig, setStoreConfig] = useState({
    store_name: '',
    industry: 'fashion', // Default
    target_audience: '',
    monthly_visitors: 0,
    currency: 'USD',
    timezone: 'America/New_York'
  });

  // Step 3: Agent Setup
  const [agentsForm, setAgentsForm] = useState({
    agents_to_enable: ['product_recommender', 'checkout_assistant'],
    agent_name: 'NeuroCommerce Assistant',
    agent_personality: 'helpful'
  });

  // Get store info from URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const storeId = params.get('store_id');
    const shopDomain = params.get('shop');
    const token = localStorage.getItem('auth_token');

    if (storeId) {
      setStore({ storeId, shopDomain: shopDomain || '', accessToken: token || '' });
      checkSetupProgress(storeId);
    }
  }, []);

  // Check setup progress
  const checkSetupProgress = async (storeId: string) => {
    try {
      const response = await fetch(`/api/setup/status/${storeId}`);
      const data = await response.json();
      setCurrentStep(Math.min(data.step_completed + 1, 4));
    } catch (err) {
      console.error('Failed to get setup status:', err);
    }
  };

  // Step 1: Account Setup
  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (accountForm.password !== accountForm.confirm_password) {
        throw new Error('Passwords do not match');
      }

      const response = await fetch('/api/setup/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          shop_name: accountForm.shop_name,
          owner_email: accountForm.owner_email,
          password: accountForm.password,
          owner_first_name: accountForm.owner_first_name,
          owner_last_name: accountForm.owner_last_name,
          shopify_shop_domain: store?.shopDomain,
          shopify_api_key: '', // From OAuth
          shopify_access_token: store?.accessToken
        })
      });

      if (!response.ok) {
        throw new Error(`Account setup failed: ${response.statusText}`);
      }

      const data = await response.json();
      localStorage.setItem('auth_token', data.access_token);
      setCurrentStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Account setup failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Store Configuration
  const handleStoreSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/setup/store', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          store_id: store?.storeId,
          ...storeConfig
        })
      });

      if (!response.ok) {
        throw new Error(`Store configuration failed: ${response.statusText}`);
      }

      setCurrentStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Store configuration failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Agent Setup
  const handleAgentsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/setup/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          store_id: store?.storeId,
          ...agentsForm
        })
      });

      if (!response.ok) {
        throw new Error(`Agent setup failed: ${response.statusText}`);
      }

      setCurrentStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent setup failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 4: Complete Setup
  const handleComplete = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/setup/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          store_id: store?.storeId
        })
      });

      if (!response.ok) {
        throw new Error(`Setup completion failed: ${response.statusText}`);
      }

      const data = await response.json();
      setCompleted(true);
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        window.location.href = data.dashboard_url;
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup completion failed');
    } finally {
      setLoading(false);
    }
  };

  const steps: SetupStep[] = [
    {
      step: 1,
      title: 'Create Account',
      description: 'Set up your NeuroCommerce account',
      completed: currentStep > 1
    },
    {
      step: 2,
      title: 'Store Configuration',
      description: 'Configure your store settings',
      completed: currentStep > 2
    },
    {
      step: 3,
      title: 'Enable Agents',
      description: 'Choose AI agents for your store',
      completed: currentStep > 3
    },
    {
      step: 4,
      title: 'Complete Setup',
      description: 'Activate and start using NeuroCommerce',
      completed: currentStep > 4
    }
  ];

  if (completed) {
    return (
      <div className="wizard-container wizard-complete">
        <div className="complete-message">
          <div className="checkmark">✓</div>
          <h1>Setup Complete!</h1>
          <p>NeuroCommerce is now active on your store.</p>
          <p className="redirect-msg">Redirecting to your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="wizard-container">
      {/* Progress Bar */}
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${(currentStep / 4) * 100}%` }}></div>
      </div>

      {/* Step Indicators */}
      <div className="step-indicators">
        {steps.map((step) => (
          <div
            key={step.step}
            className={`step-indicator ${currentStep >= step.step ? 'active' : ''} ${
              step.completed ? 'completed' : ''
            }`}
          >
            <div className="step-number">{step.completed ? '✓' : step.step}</div>
            <div className="step-label">{step.title}</div>
          </div>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Forms */}
      <div className="form-container">
        {/* Step 1: Account Setup */}
        {currentStep === 1 && (
          <form onSubmit={handleAccountSubmit} className="setup-form">
            <h2>Create Your Account</h2>
            <p className="form-description">
              Set up your NeuroCommerce account to manage your Shopify store
            </p>

            <div className="form-group">
              <label>Store Name</label>
              <input
                type="text"
                required
                placeholder="My Store"
                value={accountForm.shop_name}
                onChange={(e) => setAccountForm({ ...accountForm, shop_name: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>First Name</label>
                <input
                  type="text"
                  required
                  placeholder="John"
                  value={accountForm.owner_first_name}
                  onChange={(e) => setAccountForm({ ...accountForm, owner_first_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  required
                  placeholder="Doe"
                  value={accountForm.owner_last_name}
                  onChange={(e) => setAccountForm({ ...accountForm, owner_last_name: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={accountForm.owner_email}
                onChange={(e) => setAccountForm({ ...accountForm, owner_email: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={accountForm.password}
                  onChange={(e) => setAccountForm({ ...accountForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={accountForm.confirm_password}
                  onChange={(e) => setAccountForm({ ...accountForm, confirm_password: e.target.value })}
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        )}

        {/* Step 2: Store Configuration */}
        {currentStep === 2 && (
          <form onSubmit={handleStoreSubmit} className="setup-form">
            <h2>Configure Your Store</h2>
            <p className="form-description">
              Help us understand your store to optimize AI agents
            </p>

            <div className="form-group">
              <label>Store Name</label>
              <input
                type="text"
                required
                placeholder="My Awesome Store"
                value={storeConfig.store_name}
                onChange={(e) => setStoreConfig({ ...storeConfig, store_name: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Industry</label>
                <select
                  value={storeConfig.industry}
                  onChange={(e) => setStoreConfig({ ...storeConfig, industry: e.target.value })}
                >
                  <option value="fashion">Fashion & Apparel</option>
                  <option value="electronics">Electronics</option>
                  <option value="food">Food & Beverage</option>
                  <option value="beauty">Beauty & Personal Care</option>
                  <option value="home">Home & Garden</option>
                  <option value="sports">Sports & Outdoors</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Currency</label>
                <input
                  type="text"
                  value={storeConfig.currency}
                  onChange={(e) => setStoreConfig({ ...storeConfig, currency: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Target Audience</label>
              <input
                type="text"
                placeholder="e.g., Young professionals, Fashion enthusiasts"
                value={storeConfig.target_audience}
                onChange={(e) => setStoreConfig({ ...storeConfig, target_audience: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Monthly Visitors (estimated)</label>
                <input
                  type="number"
                  placeholder="5000"
                  value={storeConfig.monthly_visitors}
                  onChange={(e) => setStoreConfig({ ...storeConfig, monthly_visitors: parseInt(e.target.value) })}
                />
              </div>
              <div className="form-group">
                <label>Timezone</label>
                <input
                  type="text"
                  value={storeConfig.timezone}
                  onChange={(e) => setStoreConfig({ ...storeConfig, timezone: e.target.value })}
                />
              </div>
            </div>

            <div className="button-group">
              <button type="button" onClick={() => setCurrentStep(1)} className="btn btn-secondary">
                Back
              </button>
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? 'Saving...' : 'Continue'}
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Agent Setup */}
        {currentStep === 3 && (
          <form onSubmit={handleAgentsSubmit} className="setup-form">
            <h2>Enable AI Agents</h2>
            <p className="form-description">
              Choose which AI agents you want to use on your store
            </p>

            <div className="agents-grid">
              <label className="agent-checkbox">
                <input
                  type="checkbox"
                  checked={agentsForm.agents_to_enable.includes('product_recommender')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: [...agentsForm.agents_to_enable, 'product_recommender']
                      });
                    } else {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: agentsForm.agents_to_enable.filter(a => a !== 'product_recommender')
                      });
                    }
                  }}
                />
                <div className="agent-card">
                  <h3>Product Recommender</h3>
                  <p>Recommends products based on customer browsing and preferences</p>
                </div>
              </label>

              <label className="agent-checkbox">
                <input
                  type="checkbox"
                  checked={agentsForm.agents_to_enable.includes('checkout_assistant')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: [...agentsForm.agents_to_enable, 'checkout_assistant']
                      });
                    } else {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: agentsForm.agents_to_enable.filter(a => a !== 'checkout_assistant')
                      });
                    }
                  }}
                />
                <div className="agent-card">
                  <h3>Checkout Assistant</h3>
                  <p>Helps customers complete checkout with incentives and support</p>
                </div>
              </label>

              <label className="agent-checkbox">
                <input
                  type="checkbox"
                  checked={agentsForm.agents_to_enable.includes('support_bot')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: [...agentsForm.agents_to_enable, 'support_bot']
                      });
                    } else {
                      setAgentsForm({
                        ...agentsForm,
                        agents_to_enable: agentsForm.agents_to_enable.filter(a => a !== 'support_bot')
                      });
                    }
                  }}
                />
                <div className="agent-card">
                  <h3>Support Bot</h3>
                  <p>Answers customer questions about products and policies</p>
                </div>
              </label>
            </div>

            <div className="form-group">
              <label>Agent Name</label>
              <input
                type="text"
                placeholder="e.g., Alex"
                value={agentsForm.agent_name}
                onChange={(e) => setAgentsForm({ ...agentsForm, agent_name: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Agent Personality</label>
              <select
                value={agentsForm.agent_personality}
                onChange={(e) => setAgentsForm({ ...agentsForm, agent_personality: e.target.value })}
              >
                <option value="helpful">Helpful & Professional</option>
                <option value="friendly">Friendly & Casual</option>
                <option value="playful">Playful & Fun</option>
                <option value="professional">Professional & Direct</option>
              </select>
            </div>

            <div className="button-group">
              <button type="button" onClick={() => setCurrentStep(2)} className="btn btn-secondary">
                Back
              </button>
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? 'Saving...' : 'Continue'}
              </button>
            </div>
          </form>
        )}

        {/* Step 4: Completion */}
        {currentStep === 4 && (
          <div className="setup-form completion-form">
            <h2>Ready to Go!</h2>
            <p className="form-description">
              Your NeuroCommerce setup is almost complete. Click below to activate and start using AI agents on your store.
            </p>

            <div className="completion-checklist">
              <div className="checklist-item">
                <span className="checkmark">✓</span>
                <span>Account created</span>
              </div>
              <div className="checklist-item">
                <span className="checkmark">✓</span>
                <span>Store configured</span>
              </div>
              <div className="checklist-item">
                <span className="checkmark">✓</span>
                <span>AI agents enabled</span>
              </div>
              <div className="checklist-item">
                <span className="checkmark">✓</span>
                <span>Webhooks registered</span>
              </div>
            </div>

            <div className="button-group">
              <button type="button" onClick={() => setCurrentStep(3)} className="btn btn-secondary">
                Back
              </button>
              <button onClick={handleComplete} disabled={loading} className="btn btn-primary btn-large">
                {loading ? 'Activating...' : 'Activate Now'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SetupWizard;
