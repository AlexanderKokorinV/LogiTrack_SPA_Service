import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [shipments, setShipments] = useState([]);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [column, setColumn] = useState('name');
  const [condition, setCondition] = useState('contains');
  const [value, setValue] = useState('');
  const [ordering, setOrdering] = useState('');

  useEffect(() => {
    const fetchTableData = async () => {
      try {
        const response = await axios.get('/api/shipments/', {
          params: { page, column, condition, value, ordering }
        });
        setShipments(response.data.results);
        setCount(response.data.count);
      } catch (error) {
        console.error("Ошибка сети LogiTrack API:", error);
      }
    };
    fetchTableData();
  }, [page, column, condition, value, ordering]);

  const handleSort = (targetColumn) => {
    setOrdering(ordering === targetColumn ? `-${targetColumn}` : targetColumn);
    setPage(1);
  };

  // === СТИЛИ ДЛЯ ТЕМНОГО ДИЗАЙНА (ФИНАЛЬНАЯ ВЕРСИЯ) ===
  const styles = {
    bodyBg: {
      backgroundColor: '#0f172a',
      minHeight: '100vh',
      color: '#f8fafc',
      fontFamily: "'Segoe UI', Roboto, sans-serif",
      paddingBottom: '20px'
    },
    glassCard: {
      background: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '12px',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
    },
    // Отдельный стиль для карточки таблицы, чтобы растянуть её вниз
    tableCard: {
      background: '#1e293b',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '12px',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    },
    tableHeader: {
      backgroundColor: '#e0f2fe',
      color: '#0369a1',
      borderBottom: '2px solid #cbd5e1',
      fontWeight: '600',
      fontSize: '1.0rem'
    },
    tableRow: {
      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      color: '#cbd5e1'
    },
    badgeQuantity: {
      background: 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
      color: '#fff',
      padding: '4px 10px',
      borderRadius: '6px',
      fontSize: '0.8rem',
      fontWeight: '600'
    },
    badgeDistance: {
      background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
      color: '#fff',
      padding: '4px 10px',
      borderRadius: '6px',
      fontSize: '0.8rem',
      fontWeight: '600'
    },
    inputStyle: {
      backgroundColor: '#1e293b',
      border: '1px solid rgba(255, 255, 255, 0.15)',
      color: '#fff',
      borderRadius: '8px',
      fontSize: '0.85rem'
    }
  };
  // === ФУНКЦИЯ ВЫГРУЗКИ В EXCEL/CSV ===
  const exportToCSV = async () => {
    try {
      // Отправляем запрос на кастомный экшен бэкенда, передавая текущие фильтры
      const response = await axios.get('/api/shipments/export_excel/', {
        params: { column, condition, value, ordering },
        responseType: 'blob' // говорим Axios, что скачиваем бинарный файл (.xlsx)
      });

      // Скачиваем готовый файл из бэкенда
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Полный_Отчет_LogiTrack.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Ошибка при скачивании отчета с сервера:", error);
    }
  };

  return (
    <div style={styles.bodyBg}>
      <div className="container py-3">

        {/* Анимированный заголовок */}
        <div className="text-center mb-3">
          <h1 className="display-6 font-weight-bold m-0" style={{ letterSpacing: '2px', background: 'linear-gradient(to right, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            🛰️ LOGITRACK RRO
          </h1>
          {/* text-light и opacity для лучшей читаемости */}
          <p className="text-light-50 m-0" style={{ fontSize: '0.95rem', color: 'rgba(248, 250, 252, 0.7)' }}>
            Интерактивная панель для поиска и анализа рейсов
          </p>
        </div>

        {/* --- БЛОК ФИЛЬТРАЦИИ --- */}
        <div className="card p-3 mb-3" style={styles.glassCard}>
          <div className="row g-3 align-items-center">
            <div className="col-md-3">
              <label className="form-label small text-info font-weight-bold mb-1">АНАЛИЗИРУЕМАЯ КОЛОНКА</label>
              <select className="form-select text-white" style={styles.inputStyle} value={column} onChange={e => { setColumn(e.target.value); setPage(1); }}>
                <option value="name">Название (Маршрут)</option>
                <option value="quantity">Количество груза</option>
                <option value="distance">Расстояние</option>
              </select>
            </div>

            <div className="col-md-3">
              <label className="form-label small text-info font-weight-bold mb-1">ЛОГИЧЕСКОЕ УСЛОВИЕ</label>
              <select className="form-select text-white" style={styles.inputStyle} value={condition} onChange={e => { setCondition(e.target.value); setPage(1); }}>
                <option value="equals">Равно</option>
                {column === 'name' && <option value="contains">Содержит подстроку</option>}
                <option value="greater">Больше чем (&gt;)</option>
                <option value="less">Меньше чем (&lt;)</option>
              </select>
            </div>

            <div className="col-md-6">
              <label className="form-label small text-info font-weight-bold mb-1">ПОИСКОВОЕ ЗНАЧЕНИЕ</label>
              {/* Добавлен внутренний стиль для placeholder, чтобы подсказка светилась белым */}
              <input
                  type="text"
                  className="form-control text-white placeholder-light" // Добавили Bootstrap-класс
                  style={styles.inputStyle}
                  placeholder="Начните вводить данные для мгновенной фильтрации..."
                  value={value}
                  onChange={e => { setValue(e.target.value); setPage(1); }}
              />
            </div>
          </div>
        </div>
        {/* --- ТАБЛИЦА (УМЕНЬШЕННЫЕ ОТСТУПЫ) --- */}
        <div className="card p-1 mb-3" style={styles.tableCard}>
          <div className="table-responsive" style={styles.tableContainer}>
            <table className="table table-bordered align-middle m-0">
              <thead style={styles.tableHeader}>
                <tr style={styles.tableHeader}>
                  <th className="p-2 text-center" style={{ backgroundColor: '#b8f2fd', borderRight: '1px solid #cbd5e1', borderRadius: '8px 0 0 8px' }}>Дата рейса</th>
                  <th className="p-2 text-start" onClick={() => handleSort('name')} style={{ cursor: 'pointer', backgroundColor: '#b8f2fd', borderRight: '1px solid #cbd5e1' }}>
                    Маршрут {ordering === 'name' ? '▲' : ordering === '-name' ? '▼' : '↕'}
                  </th>
                  <th className="p-2 text-center" onClick={() => handleSort('quantity')} style={{ cursor: 'pointer', backgroundColor: '#b8f2fd', borderRight: '1px solid #cbd5e1' }}>
                    Количество {ordering === 'quantity' ? '▲' : ordering === '-quantity' ? '▼' : '↕'}
                  </th>
                  <th className="p-2 text-center" onClick={() => handleSort('distance')} style={{ cursor: 'pointer', backgroundColor: '#b8f2fd', borderRadius: '0 8px 8px 0' }}>
                    Расстояние {ordering === 'distance' ? '▲' : ordering === '-distance' ? '▼' : '↕'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {shipments.length > 0 ? (
                  shipments.map(shipment => (
                    <tr key={shipment.id} style={styles.tableRow}>
                      <td className="p-2 text-center text-muted small">{shipment.date}</td>
                      <td className="p-3 text-start font-weight-bold text-dark">{shipment.name}</td>
                      <td className="p-2 text-center"><span style={styles.badgeQuantity}>{shipment.quantity} ед.</span></td>
                      <td className="p-2 text-center"><span style={styles.badgeDistance}>{shipment.distance} км</span></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="text-muted p-4 text-center">
                      <div className="fs-6">🔍 Совпадений не найдено</div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* --- ТЕМНАЯ ПАНЕЛЬ ПАГИНАЦИИ --- */}
        <div className="d-flex justify-content-between align-items-center p-2 rounded" style={styles.glassCard}>

          {/* Слева: Текст мониторинга */}
          <span className="text-light small" style={{ opacity: 0.8, width: '30%' }}>
            Мониторинг: строк <strong>{count > 0 ? (page - 1) * 10 + 1 : 0}–{Math.min(page * 10, count)}</strong> из <strong>{count}</strong>
          </span>

          {/* ПО ЦЕНТРУ: кнопка выгрузки данных в excel */}
          <div className="text-center" style={{ width: '40%' }}>
            <button
              className="btn btn-sm text-white px-4 font-weight-bold"
              style={{
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 0 10px rgba(16, 185, 129, 0.2)'
              }}
              onClick={exportToCSV}
            >
              📊 Скачать отчет в Excel
            </button>
          </div>

          {/* Справа: Кнопки навигации */}
          <div className="d-flex justify-content-end" style={{ width: '30%' }}>
            <div className="btn-group">
              <button className="btn btn-outline-info btn-sm px-2" onClick={() => setPage(page - 1)} disabled={page === 1}>
                ◀ Назад
              </button>
              <span className="btn btn-dark btn-sm disabled px-3 text-white" style={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.05)', fontSize: '0.85rem' }}>
                Стр. {page}
              </span>
              <button className="btn btn-outline-info btn-sm px-2" onClick={() => setPage(page + 1)} disabled={page * 10 >= count}>
                Вперед ▶
              </button>
            </div>
          </div>

        </div>

      </div>
    </div>

  );
}

export default App;
