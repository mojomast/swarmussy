import { useState, useEffect } from 'preact/hooks';
import { fetchFileTree, fetchFileContent } from '../lib/api';
import { FileCode, Folder, FolderOpen, ChevronRight, ChevronDown } from 'lucide-preact';

export function FileBrowser() {
  const [tree, setTree] = useState<any[]>([]);
  const [currentPath, setCurrentPath] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');

  useEffect(() => {
    loadTree(currentPath);
  }, [currentPath]);

  const loadTree = async (path: string) => {
    try {
      const data = await fetchFileTree(path);
      setTree(data.items);
    } catch (e) {
      console.error(e);
    }
  };

  const handleItemClick = async (item: any) => {
    if (item.type === 'directory') {
      setCurrentPath(item.path);
    } else {
      setSelectedFile(item.path);
      try {
        const data = await fetchFileContent(item.path);
        setFileContent(data.content);
      } catch (e) {
        setFileContent('Error loading file content');
      }
    }
  };

  const goUp = () => {
    if (!currentPath) return;
    const parts = currentPath.split('/');
    parts.pop();
    setCurrentPath(parts.join('/'));
  };

  return (
    <div className="flex h-full bg-gray-900 text-gray-300">
      <div className="w-64 border-r border-gray-800 flex flex-col">
        <div className="p-3 border-b border-gray-800 flex items-center gap-2">
          <button onClick={goUp} disabled={!currentPath} className="disabled:opacity-30 hover:text-white">
            <ChevronDown className="rotate-90" size={16} />
          </button>
          <span className="text-xs font-mono truncate">{currentPath || '/root'}</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {tree.map(item => (
            <div 
              key={item.path}
              onClick={() => handleItemClick(item)}
              className="flex items-center gap-2 px-3 py-2 hover:bg-gray-800 cursor-pointer text-sm"
            >
              {item.type === 'directory' ? (
                <Folder size={16} className="text-blue-400" />
              ) : (
                <FileCode size={16} className="text-gray-400" />
              )}
              <span className="truncate">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-auto bg-gray-950 p-4 font-mono text-sm">
        {selectedFile ? (
          <pre className="whitespace-pre-wrap">{fileContent}</pre>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-600">
            Select a file to view
          </div>
        )}
      </div>
    </div>
  );
}
