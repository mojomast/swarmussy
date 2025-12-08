import React from 'react';
import { initUI } from '../ui/index';

const App = () => {
  React.useEffect(() => {
    const root = document.getElementById('root');
    if (root) {
      initUI(root);
    }
  }, []);
  return <div id="app-root" style={{ height: '100%', width: '100%' }} />;
};

export default App;
