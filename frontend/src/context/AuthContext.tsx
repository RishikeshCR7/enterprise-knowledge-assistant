import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserProfile {
  id: string;
  name: string;
  role: 'HR' | 'Engineering' | 'Finance' | 'Legal' | 'Sales' | 'Executive';
  department: 'HR' | 'Engineering' | 'Finance' | 'Legal' | 'Sales' | 'Executive';
  title: string;
  avatar: string;
  securityClearance: 'Confidential' | 'Internal' | 'Restricted' | 'All Access';
}

export const MOCK_USER_PROFILES: UserProfile[] = [
  {
    id: 'usr_hr_01',
    name: 'Sarah Jenkins',
    role: 'HR',
    department: 'HR',
    title: 'HR Operations Lead',
    avatar: '👩‍💼',
    securityClearance: 'Confidential'
  },
  {
    id: 'usr_eng_02',
    name: 'Alex Chen',
    role: 'Engineering',
    department: 'Engineering',
    title: 'Senior Software Engineer',
    avatar: '👨‍💻',
    securityClearance: 'Confidential'
  },
  {
    id: 'usr_fin_03',
    name: 'David Vance',
    role: 'Finance',
    department: 'Finance',
    title: 'Chief Financial Analyst',
    avatar: '📊',
    securityClearance: 'Confidential'
  },
  {
    id: 'usr_leg_04',
    name: 'Rachel Green',
    role: 'Legal',
    department: 'Legal',
    title: 'Senior Legal Counsel',
    avatar: '⚖️',
    securityClearance: 'Confidential'
  },
  {
    id: 'usr_sal_05',
    name: 'Marcus Brody',
    role: 'Sales',
    department: 'Sales',
    title: 'Global Sales Director',
    avatar: '💼',
    securityClearance: 'Internal'
  },
  {
    id: 'usr_exec_06',
    name: 'Elena Rostova',
    role: 'Executive',
    department: 'Executive',
    title: 'Executive Vice President (Full Clearance)',
    avatar: '👑',
    securityClearance: 'All Access'
  }
];

interface AuthContextType {
  currentUser: UserProfile;
  switchUser: (profileId: string) => void;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('eka_active_user');
    if (saved) {
      try { return JSON.parse(saved); } catch {}
    }
    return MOCK_USER_PROFILES[0]; // Default Sarah Jenkins (HR)
  });

  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('eka_theme') === 'dark';
  });

  const switchUser = (profileId: string) => {
    const selected = MOCK_USER_PROFILES.find(p => p.id === profileId);
    if (selected) {
      setCurrentUser(selected);
      localStorage.setItem('eka_active_user', JSON.stringify(selected));
    }
  };

  const toggleDarkMode = () => {
    setIsDarkMode(prev => {
      const next = !prev;
      localStorage.setItem('eka_theme', next ? 'dark' : 'light');
      return next;
    });
  };

  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [isDarkMode]);

  return (
    <AuthContext.Provider value={{ currentUser, switchUser, isDarkMode, toggleDarkMode }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
