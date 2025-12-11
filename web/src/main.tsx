import { render } from 'preact';
import { App } from './App';
import { ThemeProvider } from './components/ThemeProvider';
import './index.css';

render(
  <ThemeProvider>
    <App />
  </ThemeProvider>,
  document.getElementById('app')!
);
