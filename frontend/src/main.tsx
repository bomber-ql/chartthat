import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { ThemeProvider } from './theme';
import { I18nProvider } from './i18n';
import './styles.css';

const container = document.getElementById('root');
if (!container) {
  throw new Error('root container #root not found');
}

createRoot(container).render(
  <React.StrictMode>
    <ThemeProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
