/**
 * Enterprise Table Component
 * Reusable table for all dashboards
 */

import React from 'react';
import './EnterpriseTable.css';

const EnterpriseTable = ({ columns, data, onRowClick, emptyMessage = 'No data available' }) => {
  return (
    <div className="eds-table-container">
      <table className="eds-table">
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th key={index} style={{ width: column.width }}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem', color: 'var(--eds-color-text-muted)' }}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick && onRowClick(row)}
                style={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {columns.map((column, colIndex) => (
                  <td key={colIndex}>
                    {column.render ? column.render(row) : row[column.accessor]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default EnterpriseTable;

