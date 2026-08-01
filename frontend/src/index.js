import React from 'react';
import ReactDOM from 'react-dom/client';
import './bootstrap.min.css';
import App from './App';

// ЕДИНЫЙ БЛОК НАСТРОЕК СТИЛЕЙ ДЛЯ БРАУЗЕРА
const style = document.createElement('style');
style.innerHTML = `
  /* 1. Делаем подсказку в инпуте светлой */
  input.form-control::placeholder {
    color: rgba(255, 255, 255, 0.5) !important;
    opacity: 1 !important;
  }

  /* 2. Вертикальная сетка для столбцов и шапки */
  .table-bordered th, .table-bordered td {
    border: 1px solid #cbd5e1 !important;
  }

  /* 3. Горизонтальная сетка между строками */
  .table tbody tr td {
    border: 1px solid #cbd5e1 !important;
  }

  /* 4. Белый фон для всего списка значений */
  .table-bordered tbody tr {
    background-color: #ffffff !important;
  }
`;
document.head.appendChild(style);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);