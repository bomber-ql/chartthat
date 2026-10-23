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

// v1.22 内容区双轨：清空 index.html 内嵌的静态英文 SEO 内容（爬虫可见），
// 浏览器端由 App 经 createPortal 渲染五语言版本到同一容器。
document.getElementById('site-content')?.replaceChildren();

createRoot(container).render(
  <React.StrictMode>
    <ThemeProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
