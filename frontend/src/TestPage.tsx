import React from 'react';

export const TestPage = () => {
  const [timestamp, setTimestamp] = React.useState(new Date().toLocaleString());
  
  React.useEffect(() => {
    console.log('TestPage mounted at:', timestamp);
    
    return () => {
      console.log('TestPage unmounted at:', new Date().toLocaleString());
    };
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>React Test Page - HMR Fixed Configuration</h1>
      <p>This is a minimal React component to test refresh behavior and HMR functionality.</p>
      <p><strong>Mounted at:</strong> {timestamp}</p>
      <p><strong>Current time:</strong> {new Date().toLocaleString()}</p>
      
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
        <h3>Debug Info:</h3>
        <p>User Agent: {navigator.userAgent}</p>
        <p>Current URL: {window.location.href}</p>
      </div>
    </div>
  );
};