import { useState } from 'react';

export default function AletheiaPopupPrototype() {
  const [view, setView] = useState('main'); // 'main' | 'manage' | 'confirm'
  const [isActive, setIsActive] = useState(false);
  const [allowlist, setAllowlist] = useState(['wsj.com', 'nytimes.com', 'economist.com']);
  const [selected, setSelected] = useState(new Set());
  const currentDomain = 'wsj.com';

  const toggleActive = () => {
    if (isActive) {
      setAllowlist(allowlist.filter(d => d !== currentDomain));
    } else {
      if (!allowlist.includes(currentDomain)) {
        setAllowlist([...allowlist, currentDomain]);
      }
    }
    setIsActive(!isActive);
  };

  const toggleSelect = (domain) => {
    const newSelected = new Set(selected);
    if (newSelected.has(domain)) {
      newSelected.delete(domain);
    } else {
      newSelected.add(domain);
    }
    setSelected(newSelected);
  };

  const removeSelected = () => {
    const newAllowlist = allowlist.filter(d => !selected.has(d));
    setAllowlist(newAllowlist);
    setSelected(new Set());
    if (selected.has(currentDomain)) {
      setIsActive(false);
    }
  };

  const clearAll = () => {
    setAllowlist([]);
    setSelected(new Set());
    setIsActive(false);
    setView('main');
  };

  // Design tokens
  const colors = {
    primary: '#22C55E',
    primaryHover: '#16A34A',
    danger: '#EF4444',
    dangerHover: '#DC2626',
    text: '#1F2937',
    textSecondary: '#6B7280',
    bg: '#FFFFFF',
    bgSecondary: '#F9FAFB',
    border: '#E5E7EB',
  };

  const PopupContainer = ({ children }) => (
    <div style={{
      width: 280,
      backgroundColor: colors.bg,
      borderRadius: 12,
      boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      overflow: 'hidden',
      border: `1px solid ${colors.border}`,
    }}>
      {children}
    </div>
  );

  const Badge = () => (
    <span style={{
      position: 'absolute',
      top: -4,
      right: -4,
      backgroundColor: colors.primary,
      color: 'white',
      fontSize: 10,
      fontWeight: 700,
      width: 16,
      height: 16,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>✓</span>
  );

  // Main View
  const MainView = () => (
    <div style={{ padding: 24 }}>
      {/* Logo placeholder */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 20,
        position: 'relative',
      }}>
        <div style={{
          width: 40,
          height: 40,
          borderRadius: 8,
          backgroundColor: colors.primary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 700,
          fontSize: 20,
          position: 'relative',
        }}>
          A
          {isActive && <Badge />}
        </div>
      </div>

      {/* Current domain */}
      <div style={{
        backgroundColor: colors.bgSecondary,
        borderRadius: 8,
        padding: '12px 16px',
        textAlign: 'center',
        marginBottom: 20,
        border: `1px solid ${colors.border}`,
      }}>
        <div style={{
          fontSize: 11,
          color: colors.textSecondary,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: 4,
        }}>
          Current Domain
        </div>
        <div style={{
          fontSize: 16,
          fontWeight: 600,
          color: colors.text,
        }}>
          {currentDomain}
        </div>
      </div>

      {/* Power button */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <button
          onClick={toggleActive}
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            border: isActive ? 'none' : `3px solid ${colors.border}`,
            backgroundColor: isActive ? colors.primary : 'transparent',
            color: isActive ? 'white' : colors.textSecondary,
            fontSize: 28,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            marginBottom: 12,
          }}
          onMouseEnter={(e) => {
            if (isActive) {
              e.target.style.backgroundColor = colors.primaryHover;
            } else {
              e.target.style.borderColor = colors.textSecondary;
            }
          }}
          onMouseLeave={(e) => {
            if (isActive) {
              e.target.style.backgroundColor = colors.primary;
            } else {
              e.target.style.borderColor = colors.border;
            }
          }}
        >
          ⏻
        </button>
        <div style={{
          fontSize: 14,
          color: isActive ? colors.primary : colors.textSecondary,
          fontWeight: 500,
        }}>
          Aletheia is <strong>{isActive ? 'ACTIVE' : 'INACTIVE'}</strong>
        </div>
        <div style={{
          fontSize: 12,
          color: colors.textSecondary,
          marginTop: 2,
        }}>
          on this domain
        </div>
      </div>

      {/* Manage link */}
      <button
        onClick={() => setView('manage')}
        style={{
          width: '100%',
          padding: '12px 16px',
          backgroundColor: 'transparent',
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          color: colors.text,
          fontSize: 14,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'background-color 0.15s ease',
        }}
        onMouseEnter={(e) => e.target.style.backgroundColor = colors.bgSecondary}
        onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
      >
        <span>Manage Allowlist</span>
        <span style={{ color: colors.textSecondary }}>→</span>
      </button>
    </div>
  );

  // Management View
  const ManageView = () => (
    <div>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: `1px solid ${colors.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <button
          onClick={() => { setView('main'); setSelected(new Set()); }}
          style={{
            background: 'none',
            border: 'none',
            fontSize: 18,
            cursor: 'pointer',
            color: colors.textSecondary,
            padding: 0,
          }}
        >
          ←
        </button>
        <span style={{
          fontSize: 16,
          fontWeight: 600,
          color: colors.text,
        }}>
          Allowlist
        </span>
        <span style={{
          marginLeft: 'auto',
          fontSize: 12,
          color: colors.textSecondary,
          backgroundColor: colors.bgSecondary,
          padding: '2px 8px',
          borderRadius: 12,
        }}>
          {allowlist.length} {allowlist.length === 1 ? 'site' : 'sites'}
        </span>
      </div>

      {/* List */}
      <div style={{
        maxHeight: 180,
        overflowY: 'auto',
        borderBottom: `1px solid ${colors.border}`,
      }}>
        {allowlist.length === 0 ? (
          <div style={{
            padding: 24,
            textAlign: 'center',
            color: colors.textSecondary,
            fontSize: 14,
          }}>
            No domains allowlisted
          </div>
        ) : (
          allowlist.map((domain) => (
            <label
              key={domain}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px 20px',
                cursor: 'pointer',
                backgroundColor: selected.has(domain) ? colors.bgSecondary : 'transparent',
                borderBottom: `1px solid ${colors.border}`,
              }}
            >
              <input
                type="checkbox"
                checked={selected.has(domain)}
                onChange={() => toggleSelect(domain)}
                style={{
                  width: 16,
                  height: 16,
                  marginRight: 12,
                  accentColor: colors.primary,
                }}
              />
              <span style={{
                fontSize: 14,
                color: colors.text,
              }}>
                {domain}
              </span>
              {domain === currentDomain && (
                <span style={{
                  marginLeft: 'auto',
                  fontSize: 10,
                  color: colors.primary,
                  backgroundColor: `${colors.primary}15`,
                  padding: '2px 6px',
                  borderRadius: 4,
                  fontWeight: 500,
                }}>
                  current
                </span>
              )}
            </label>
          ))
        )}
      </div>

      {/* Actions */}
      <div style={{ padding: 16 }}>
        <button
          onClick={removeSelected}
          disabled={selected.size === 0}
          style={{
            width: '100%',
            padding: '10px 16px',
            backgroundColor: selected.size > 0 ? colors.text : colors.bgSecondary,
            color: selected.size > 0 ? 'white' : colors.textSecondary,
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: selected.size > 0 ? 'pointer' : 'not-allowed',
            marginBottom: 12,
            transition: 'background-color 0.15s ease',
          }}
        >
          Remove Selected {selected.size > 0 && `(${selected.size})`}
        </button>

        <button
          onClick={() => setView('confirm')}
          style={{
            width: '100%',
            padding: '10px 16px',
            backgroundColor: 'transparent',
            color: colors.danger,
            border: `1px solid ${colors.danger}`,
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = colors.danger;
            e.target.style.color = 'white';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'transparent';
            e.target.style.color = colors.danger;
          }}
        >
          ⚠ Clear All Data
        </button>
      </div>
    </div>
  );

  // Confirm Dialog
  const ConfirmView = () => (
    <div style={{ padding: 24, textAlign: 'center' }}>
      <div style={{
        width: 48,
        height: 48,
        borderRadius: '50%',
        backgroundColor: `${colors.danger}15`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 16px',
        fontSize: 24,
      }}>
        ⚠
      </div>
      <div style={{
        fontSize: 16,
        fontWeight: 600,
        color: colors.text,
        marginBottom: 8,
      }}>
        Clear All Data?
      </div>
      <div style={{
        fontSize: 14,
        color: colors.textSecondary,
        marginBottom: 20,
        lineHeight: 1.5,
      }}>
        This will remove all allowlisted domains. This action cannot be undone.
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        <button
          onClick={() => setView('manage')}
          style={{
            flex: 1,
            padding: '10px 16px',
            backgroundColor: colors.bgSecondary,
            color: colors.text,
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          onClick={clearAll}
          style={{
            flex: 1,
            padding: '10px 16px',
            backgroundColor: colors.danger,
            color: 'white',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          Clear All
        </button>
      </div>
    </div>
  );

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#F3F4F6',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
      gap: 16,
    }}>
      <div style={{
        fontSize: 12,
        color: '#6B7280',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
      }}>
        Aletheia Popup Prototype
      </div>

      <PopupContainer>
        {view === 'main' && <MainView />}
        {view === 'manage' && <ManageView />}
        {view === 'confirm' && <ConfirmView />}
      </PopupContainer>

      <div style={{
        fontSize: 12,
        color: '#9CA3AF',
        marginTop: 8,
      }}>
        Click power button and "Manage Allowlist" to explore
      </div>
    </div>
  );
}
