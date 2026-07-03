import React from 'react';

const SkeletonLoader = () => {
  return (
    <div className="message-wrapper bot">
      <div className="message-bubble bot" style={{ padding: '1rem', minWidth: '200px' }}>
        <div className="skeleton-line" style={{ width: '90%' }}></div>
        <div className="skeleton-line" style={{ width: '75%' }}></div>
        <div className="skeleton-line short"></div>
        <div className="skeleton-line medium"></div>
        <div className="skeleton-line" style={{ width: '60%' }}></div>
      </div>
    </div>
  );
};

export default SkeletonLoader;