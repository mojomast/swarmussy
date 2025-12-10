import { useState, useEffect, useCallback, useRef } from 'preact/hooks';
import { fetchState, fetchSettings, fetchDevussyStatus } from '../lib/api';

export function useSwarm() {
  const [messages, setMessages] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [status, setStatus] = useState<any>({});
  const [project, setProject] = useState<any>(null);
  const [settings, setSettings] = useState<any>({});
  const [devussy, setDevussy] = useState<any>({});
  const [connected, setConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);

  const refreshState = useCallback(async () => {
    try {
      const data = await fetchState();
      setAgents(data.agents);
      setTasks(data.tasks);
      setStatus(data.status);
      setProject(data.project);
      
      const setts = await fetchSettings();
      setSettings(setts);
      
      const dev = await fetchDevussyStatus();
      setDevussy(dev);
    } catch (e) {
      console.error('Failed to fetch state', e);
    }
  }, []);

  useEffect(() => {
    refreshState();
    
    // Connect WebSocket
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);
      
      ws.onopen = () => {
        setConnected(true);
        console.log('WS Connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
          setMessages(prev => [...prev, data.payload]);
        } else if (data.type === 'status') {
          // Trigger a refresh or just show a toast?
          // For now, let's refresh status periodically or on specific events
          refreshState();
        }
      };
      
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      
      wsRef.current = ws;
    };
    
    connect();
    
    return () => {
      wsRef.current?.close();
    };
  }, [refreshState]);

  return {
    messages,
    agents,
    tasks,
    status,
    project,
    settings,
    devussy,
    connected,
    refreshState
  };
}
